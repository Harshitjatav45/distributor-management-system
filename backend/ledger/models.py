from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from customer.models import Customer
from supplier.models import Supplier


class Ledger(models.Model):
    REFERENCE_TYPE_CHOICES = [
        ('OPENING', 'Opening'),
        ('PURCHASE', 'Purchase'),
        ('SALES', 'Sales'),
        ('PAYMENT_IN', 'Payment In'),
        ('PAYMENT_OUT', 'Payment Out'),
    ]

    ENTRY_TYPE_CHOICES = [
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
    ]

    transaction_date = models.DateField()
    reference_type = models.CharField(max_length=20, choices=REFERENCE_TYPE_CHOICES)
    reference_id = models.PositiveIntegerField(blank=True, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, blank=True, null=True, related_name='ledger_entries')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, blank=True, null=True, related_name='ledger_entries')
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    balance = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='ledger_amount_gt_0'),
            models.CheckConstraint(condition=models.Q(balance__gte=0), name='ledger_balance_gte_0'),
            # Mirrors the customer-XOR-supplier rule already enforced in
            # LedgerSerializer.validate() - see payment/models.py for the
            # same pattern.
            models.CheckConstraint(
                condition=(
                    (models.Q(customer__isnull=False) & models.Q(supplier__isnull=True))
                    | (models.Q(customer__isnull=True) & models.Q(supplier__isnull=False))
                ),
                name='ledger_customer_xor_supplier',
            ),
        ]

    def __str__(self):
        return f"{self.reference_type} - {self.amount}"
