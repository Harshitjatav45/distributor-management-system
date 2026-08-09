import logging
from decimal import Decimal
from django.db.models import Sum
from rest_framework.exceptions import ValidationError
from stock.models import Stock
from ledger.models import Ledger
from customer.models import Customer

logger = logging.getLogger(__name__)


def _materials_with_quantity(sales):
    """Aggregate quantity per material across this Sales' line items, in a
    deterministic ascending material_id order (required for deadlock-free
    Stock row locking). Aggregating first means a material appearing on more
    than one line within the same Sales is only locked/updated once, with the
    combined quantity - not once per line.
    """
    return list(
        sales.items.values('material_id', 'material__material_name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('material_id')
    )


def deduct_sales_stock(sales):
    """Deduct stock for every SalesItem on a Sales moving DRAFT -> CONFIRMED.

    Two-pass: validate every material's availability first (locking each
    Stock row along the way), only then apply any deduction. A shortage on
    any single material rejects the whole confirmation with none deducted.
    """
    lines = _materials_with_quantity(sales)

    locked_stocks = {}
    for line in lines:
        material_id = line['material_id']
        required = line['total_quantity']
        stock = Stock.objects.select_for_update().filter(material_id=material_id).first()
        available = stock.available_stock if stock is not None else Decimal('0')

        if stock is None or available < required:
            shortage = required - available
            raise ValidationError({
                'items': (
                    f"Insufficient stock for '{line['material__material_name']}': "
                    f"available {available}, required {required}, short by {shortage}."
                )
            })
        locked_stocks[material_id] = stock

    for line in lines:
        stock = locked_stocks[line['material_id']]
        stock.current_stock = stock.current_stock - line['total_quantity']
        stock.available_stock = stock.available_stock - line['total_quantity']
        stock.save()


def restore_sales_stock(sales):
    """Restore stock for every SalesItem on a Sales moving CONFIRMED -> CANCELLED.

    Restoring (adding back) can never itself produce a negative result, so
    unlike a Purchase reversal this needs no "would go negative" guard.
    """
    lines = _materials_with_quantity(sales)

    locked_stocks = {}
    for line in lines:
        material_id = line['material_id']
        stock = Stock.objects.select_for_update().get(material_id=material_id)
        locked_stocks[material_id] = stock

    for line in lines:
        stock = locked_stocks[line['material_id']]
        stock.current_stock = stock.current_stock + line['total_quantity']
        stock.available_stock = stock.available_stock + line['total_quantity']
        stock.save()


def _get_previous_customer_balance(customer):
    """Caller must already hold a select_for_update() lock on `customer`.

    Reuses the exact running-balance convention already established for
    Supplier in purchase/services.py: previous balance is the `balance` of
    the most recent Ledger row for this party (insertion order via -id, not
    transaction_date), falling back to the party's opening balance if no
    prior Ledger row exists. DEBIT/CREDIT roles are mirrored for a Customer
    (a debtor) versus a Supplier (a creditor): DEBIT is the increasing
    direction here, so opening_balance_type == 'DEBIT' contributes positively.
    """
    last_entry = Ledger.objects.filter(customer=customer).order_by('-id').first()
    if last_entry is not None:
        return last_entry.balance
    if customer.opening_balance_type == 'DEBIT':
        return customer.opening_balance
    return -customer.opening_balance


def post_sales_confirmation_ledger_entry(sales):
    """Create the DEBIT Ledger entry for a Sales moving DRAFT -> CONFIRMED.

    Locks the Customer row before reading/computing the running balance so
    that two different Sales for the same Customer, confirmed concurrently,
    serialize through this lock instead of racing on a stale "previous
    balance". Called only after Stock has already been successfully deducted.
    """
    customer = Customer.objects.select_for_update().get(pk=sales.customer_id)

    previous_balance = _get_previous_customer_balance(customer)
    new_balance = previous_balance + sales.grand_total

    Ledger.objects.create(
        transaction_date=sales.sales_date,
        reference_type='SALES',
        reference_id=sales.id,
        customer=customer,
        entry_type='DEBIT',
        amount=sales.grand_total,
        balance=new_balance,
        remarks=f"Sales {sales.sales_number} confirmed.",
    )


def post_sales_cancellation_ledger_entry(sales):
    """Create the offsetting CREDIT Ledger entry for a Sales moving CONFIRMED -> CANCELLED.

    Never deletes/mutates the original DEBIT entry - posts a second, opposite
    entry against the same reference_type/reference_id instead. Locks the
    Customer row for the same reason as the confirmation path.
    """
    customer = Customer.objects.select_for_update().get(pk=sales.customer_id)

    already_reversed = Ledger.objects.filter(
        customer=customer,
        reference_type='SALES',
        reference_id=sales.id,
        entry_type='CREDIT',
    ).exists()
    if already_reversed:
        return

    previous_balance = _get_previous_customer_balance(customer)
    new_balance = previous_balance - sales.grand_total

    if new_balance < 0:
        raise ValidationError({
            'status': (
                f"Cannot cancel: reversing sales '{sales.sales_number}' would make "
                f"customer '{customer.customer_name}' outstanding balance negative "
                f"(current balance: {previous_balance}, reversal amount: {sales.grand_total})."
            )
        })

    Ledger.objects.create(
        transaction_date=sales.sales_date,
        reference_type='SALES',
        reference_id=sales.id,
        customer=customer,
        entry_type='CREDIT',
        amount=sales.grand_total,
        balance=new_balance,
        remarks=f"Reversal: Sales {sales.sales_number} cancelled.",
    )


def confirm_sales(sales):
    """Orchestrates DRAFT -> CONFIRMED: validate, then Stock, then Ledger, in that order."""
    if sales.grand_total is None or sales.grand_total <= 0:
        raise ValidationError({
            'grand_total': 'Sales grand_total must be greater than zero to confirm.'
        })
    deduct_sales_stock(sales)
    post_sales_confirmation_ledger_entry(sales)
    logger.info("Sales confirmed: sales_number=%s customer_id=%s", sales.sales_number, sales.customer_id)


def cancel_sales(sales):
    """Orchestrates CONFIRMED -> CANCELLED: guard against an active Dispatch,
    then reverse Stock, then reverse Ledger.

    Guard rationale: once a Dispatch exists, the goods may have already
    physically left the warehouse (or been delivered). Restoring Stock in
    that case would create a false inventory record. This check runs here,
    inside the same locked Sales transaction perform_update() already
    establishes, so it's race-safe against a concurrent Dispatch creation
    without needing a second, separate lock - Dispatch creation itself locks
    this same Sales row first (see dispatch/services.py), so the two
    operations always serialize against each other through that shared lock.
    """
    from dispatch.models import Dispatch

    has_blocking_dispatch = Dispatch.objects.filter(sales=sales).exclude(status='CANCELLED').exists()
    if has_blocking_dispatch:
        raise ValidationError({
            'status': (
                f"Cannot cancel sales '{sales.sales_number}': an active or completed Dispatch "
                f"exists for this order. Cancel the Dispatch first if it has not been delivered."
            )
        })

    restore_sales_stock(sales)
    post_sales_cancellation_ledger_entry(sales)
    logger.info("Sales cancelled: sales_number=%s customer_id=%s", sales.sales_number, sales.customer_id)
