from django.core.validators import MinValueValidator
from django.db import models


class Supplier(models.Model):
    SUPPLIER_TYPE_CHOICES = [
        ('MANUFACTURER', 'Manufacturer'),
        ('DISTRIBUTOR', 'Distributor'),
        ('WHOLESALER', 'Wholesaler'),
        ('RETAIL_SUPPLIER', 'Retail Supplier'),
        ('LOCAL_TRADER', 'Local Trader'),
    ]

    BALANCE_TYPE_CHOICES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ]

    supplier_name = models.CharField(max_length=255)
    supplier_code = models.CharField(max_length=50, unique=True)
    supplier_type = models.CharField(max_length=30, choices=SUPPLIER_TYPE_CHOICES, blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    alternate_mobile = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    opening_balance_type = models.CharField(max_length=20, choices=BALANCE_TYPE_CHOICES, default='CREDIT')
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    credit_days = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_holder_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=30, blank=True, null=True)
    ifsc_code = models.CharField(max_length=11, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(opening_balance__gte=0), name='supplier_opening_balance_gte_0'),
            models.CheckConstraint(
                condition=models.Q(credit_limit__isnull=True) | models.Q(credit_limit__gte=0),
                name='supplier_credit_limit_gte_0',
            ),
            models.CheckConstraint(condition=models.Q(credit_days__gte=0), name='supplier_credit_days_gte_0'),
        ]

    def __str__(self):
        return f"{self.supplier_name} ({self.supplier_code})"
