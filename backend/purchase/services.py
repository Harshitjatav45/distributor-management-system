import logging
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from stock.models import Stock
from ledger.models import Ledger
from supplier.models import Supplier

logger = logging.getLogger(__name__)


def _effective_quantity(item):
    return item.received_quantity if item.received_quantity is not None else item.quantity


def apply_purchase_confirmation(purchase):
    """Increase stock for every item on a Purchase moving DRAFT -> CONFIRMED.

    Items are processed in ascending material_id order (mirroring Sales'
    _materials_with_quantity) so that two different Purchases sharing
    overlapping materials, confirmed concurrently, always acquire their
    Stock row locks in the same order - preventing a lock-ordering deadlock.
    """
    for item in purchase.items.select_related('material').order_by('material_id').all():
        qty = _effective_quantity(item)
        stock, _ = Stock.objects.select_for_update().get_or_create(material=item.material)

        old_qty = stock.current_stock
        old_average = stock.average_purchase_price or Decimal('0')
        new_qty = old_qty + qty

        if new_qty > 0:
            new_average = ((old_average * old_qty) + (item.rate * qty)) / new_qty
        else:
            new_average = item.rate

        stock.current_stock = new_qty
        stock.available_stock = stock.available_stock + qty
        stock.last_purchase_price = item.rate
        stock.average_purchase_price = new_average
        stock.save()


def reverse_purchase_confirmation(purchase):
    """Reverse stock for every item on a Purchase moving CONFIRMED -> CANCELLED.

    average_purchase_price / last_purchase_price are intentionally NOT reversed here:
    correctly undoing a moving weighted average requires a movement history
    (a future StockMovement ledger), which this implementation does not add.
    Only current_stock / available_stock are reversed.
    """
    items = list(purchase.items.select_related('material').order_by('material_id').all())

    # First pass: validate the reversal won't drive any material negative.
    for item in items:
        qty = _effective_quantity(item)
        stock = Stock.objects.select_for_update().filter(material=item.material).first()
        if stock is None:
            raise ValidationError({
                'status': f"Cannot cancel: no stock record found for '{item.material.material_name}'."
            })
        if stock.current_stock - qty < 0 or stock.available_stock - qty < 0:
            raise ValidationError({
                'status': (
                    f"Cannot cancel: reversing this purchase would make stock for "
                    f"'{item.material.material_name}' negative "
                    f"(current: {stock.current_stock}, available: {stock.available_stock}, "
                    f"reversal amount: {qty})."
                )
            })

    # Second pass: apply the reversal now that every line has been validated.
    for item in items:
        qty = _effective_quantity(item)
        stock = Stock.objects.select_for_update().get(material=item.material)
        stock.current_stock = stock.current_stock - qty
        stock.available_stock = stock.available_stock - qty
        stock.save()


def _get_previous_supplier_balance(supplier):
    """Caller must already hold a select_for_update() lock on `supplier`."""
    last_entry = Ledger.objects.filter(supplier=supplier).order_by('-id').first()
    if last_entry is not None:
        return last_entry.balance
    if supplier.opening_balance_type == 'CREDIT':
        return supplier.opening_balance
    return -supplier.opening_balance


def post_purchase_confirmation_ledger_entry(purchase):
    """Create the CREDIT Ledger entry for a Purchase moving DRAFT -> CONFIRMED.

    Locks the Supplier row before reading/computing the running balance so that
    two different Purchases for the same Supplier, confirmed concurrently,
    serialize through this lock instead of racing on a stale "previous balance".
    """
    supplier = Supplier.objects.select_for_update().get(pk=purchase.supplier_id)

    previous_balance = _get_previous_supplier_balance(supplier)
    new_balance = previous_balance + purchase.grand_total

    Ledger.objects.create(
        transaction_date=purchase.purchase_date,
        reference_type='PURCHASE',
        reference_id=purchase.id,
        supplier=supplier,
        entry_type='CREDIT',
        amount=purchase.grand_total,
        balance=new_balance,
        remarks=f"Purchase {purchase.purchase_number} confirmed.",
    )


def post_purchase_cancellation_ledger_entry(purchase):
    """Create the offsetting DEBIT Ledger entry for a Purchase moving CONFIRMED -> CANCELLED.

    Never deletes/mutates the original CREDIT entry - posts a second, opposite entry
    against the same reference_type/reference_id instead. Locks the Supplier row for
    the same reason as the confirmation path.
    """
    supplier = Supplier.objects.select_for_update().get(pk=purchase.supplier_id)

    already_reversed = Ledger.objects.filter(
        supplier=supplier,
        reference_type='PURCHASE',
        reference_id=purchase.id,
        entry_type='DEBIT',
    ).exists()
    if already_reversed:
        return

    previous_balance = _get_previous_supplier_balance(supplier)
    new_balance = previous_balance - purchase.grand_total

    if new_balance < 0:
        raise ValidationError({
            'status': (
                f"Cannot cancel: reversing purchase '{purchase.purchase_number}' would make "
                f"supplier '{supplier.supplier_name}' payable balance negative "
                f"(current balance: {previous_balance}, reversal amount: {purchase.grand_total})."
            )
        })

    Ledger.objects.create(
        transaction_date=purchase.purchase_date,
        reference_type='PURCHASE',
        reference_id=purchase.id,
        supplier=supplier,
        entry_type='DEBIT',
        amount=purchase.grand_total,
        balance=new_balance,
        remarks=f"Reversal: Purchase {purchase.purchase_number} cancelled.",
    )


def confirm_purchase(purchase):
    """Orchestrates DRAFT -> CONFIRMED: validate, then Stock, then Ledger, in that order."""
    if purchase.grand_total is None or purchase.grand_total <= 0:
        raise ValidationError({
            'grand_total': 'Purchase grand_total must be greater than zero to confirm.'
        })
    apply_purchase_confirmation(purchase)
    post_purchase_confirmation_ledger_entry(purchase)
    logger.info("Purchase confirmed: purchase_number=%s supplier_id=%s", purchase.purchase_number, purchase.supplier_id)


def cancel_purchase(purchase):
    """Orchestrates CONFIRMED -> CANCELLED: reverse Stock, then reverse Ledger."""
    reverse_purchase_confirmation(purchase)
    post_purchase_cancellation_ledger_entry(purchase)
    logger.info("Purchase cancelled: purchase_number=%s supplier_id=%s", purchase.purchase_number, purchase.supplier_id)
