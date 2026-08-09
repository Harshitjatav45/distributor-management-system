from rest_framework.exceptions import ValidationError
from ledger.models import Ledger
from customer.models import Customer
from supplier.models import Supplier


def get_previous_customer_balance(customer):
    """Caller must already hold a select_for_update() lock on `customer`.

    Reuses the exact running-balance convention already established for
    Sales -> Ledger automation: previous balance is the `balance` of the
    most recent Ledger row for this party (insertion order via -id), falling
    back to the party's opening balance if no prior Ledger row exists.
    """
    last_entry = Ledger.objects.filter(customer=customer).order_by('-id').first()
    if last_entry is not None:
        return last_entry.balance
    if customer.opening_balance_type == 'DEBIT':
        return customer.opening_balance
    return -customer.opening_balance


def get_previous_supplier_balance(supplier):
    """Caller must already hold a select_for_update() lock on `supplier`.

    Mirrors get_previous_customer_balance(), reusing the exact convention
    already established for Purchase -> Ledger automation.
    """
    last_entry = Ledger.objects.filter(supplier=supplier).order_by('-id').first()
    if last_entry is not None:
        return last_entry.balance
    if supplier.opening_balance_type == 'CREDIT':
        return supplier.opening_balance
    return -supplier.opening_balance


def lock_and_validate_payment_in(customer_id, amount):
    """Locks the Customer row, computes the previous balance, and rejects
    overpayment. Returns (customer, new_balance)."""
    customer = Customer.objects.select_for_update().get(pk=customer_id)
    previous_balance = get_previous_customer_balance(customer)
    new_balance = previous_balance - amount

    if new_balance < 0:
        raise ValidationError({
            'amount': (
                f"Payment of {amount} exceeds customer '{customer.customer_name}' "
                f"outstanding balance of {previous_balance}."
            )
        })
    return customer, new_balance


def lock_and_validate_payment_out(supplier_id, amount):
    """Locks the Supplier row, computes the previous balance, and rejects
    overpayment. Returns (supplier, new_balance)."""
    supplier = Supplier.objects.select_for_update().get(pk=supplier_id)
    previous_balance = get_previous_supplier_balance(supplier)
    new_balance = previous_balance - amount

    if new_balance < 0:
        raise ValidationError({
            'amount': (
                f"Payment of {amount} exceeds supplier '{supplier.supplier_name}' "
                f"payable balance of {previous_balance}."
            )
        })
    return supplier, new_balance


def post_payment_in_ledger_entry(payment, customer, new_balance):
    Ledger.objects.create(
        transaction_date=payment.payment_date,
        reference_type='PAYMENT_IN',
        reference_id=payment.id,
        customer=customer,
        entry_type='CREDIT',
        amount=payment.amount,
        balance=new_balance,
        remarks=f"Payment {payment.payment_number} received from customer.",
    )


def post_payment_out_ledger_entry(payment, supplier, new_balance):
    Ledger.objects.create(
        transaction_date=payment.payment_date,
        reference_type='PAYMENT_OUT',
        reference_id=payment.id,
        supplier=supplier,
        entry_type='DEBIT',
        amount=payment.amount,
        balance=new_balance,
        remarks=f"Payment {payment.payment_number} paid to supplier.",
    )


def cancel_payment_in(payment):
    customer = Customer.objects.select_for_update().get(pk=payment.customer_id)

    already_reversed = Ledger.objects.filter(
        customer=customer,
        reference_type='PAYMENT_IN',
        reference_id=payment.id,
        entry_type='DEBIT',
    ).exists()
    if already_reversed:
        return

    previous_balance = get_previous_customer_balance(customer)
    new_balance = previous_balance + payment.amount

    Ledger.objects.create(
        transaction_date=payment.payment_date,
        reference_type='PAYMENT_IN',
        reference_id=payment.id,
        customer=customer,
        entry_type='DEBIT',
        amount=payment.amount,
        balance=new_balance,
        remarks=f"Reversal: Payment {payment.payment_number} cancelled.",
    )


def cancel_payment_out(payment):
    supplier = Supplier.objects.select_for_update().get(pk=payment.supplier_id)

    already_reversed = Ledger.objects.filter(
        supplier=supplier,
        reference_type='PAYMENT_OUT',
        reference_id=payment.id,
        entry_type='CREDIT',
    ).exists()
    if already_reversed:
        return

    previous_balance = get_previous_supplier_balance(supplier)
    new_balance = previous_balance + payment.amount

    Ledger.objects.create(
        transaction_date=payment.payment_date,
        reference_type='PAYMENT_OUT',
        reference_id=payment.id,
        supplier=supplier,
        entry_type='CREDIT',
        amount=payment.amount,
        balance=new_balance,
        remarks=f"Reversal: Payment {payment.payment_number} cancelled.",
    )


def cancel_payment(payment):
    """Orchestrates CONFIRMED -> CANCELLED for either payment direction."""
    if payment.payment_type == 'PAYMENT_IN':
        cancel_payment_in(payment)
    else:
        cancel_payment_out(payment)
