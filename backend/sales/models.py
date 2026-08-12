from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from customer.models import Customer
from material.models import Material


class Sales(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    ]

    sales_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales')
    sales_date = models.DateField()
    invoice_number = models.CharField(max_length=50, blank=True, null=True)
    invoice_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    # round_off deliberately unconstrained - see purchase/models.py for why.
    round_off = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(total_amount__gte=0), name='sales_total_amount_gte_0'),
            models.CheckConstraint(condition=models.Q(discount_amount__gte=0), name='sales_discount_amount_gte_0'),
            models.CheckConstraint(condition=models.Q(gst_amount__gte=0), name='sales_gst_amount_gte_0'),
            models.CheckConstraint(condition=models.Q(grand_total__gte=0), name='sales_grand_total_gte_0'),
        ]

    def __str__(self):
        return self.sales_number


class SalesItem(models.Model):
    sales = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name='sales_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])
    unit = models.CharField(max_length=50, choices=Material.UNIT_CHOICES)
    rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, validators=[MinValueValidator(0)])
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    hsn_code_snapshot = models.CharField(max_length=20, blank=True, null=True)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    line_total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name='salesitem_quantity_gt_0'),
            models.CheckConstraint(condition=models.Q(rate__gte=0), name='salesitem_rate_gte_0'),
            models.CheckConstraint(condition=models.Q(discount_percentage__gte=0), name='salesitem_discount_percentage_gte_0'),
            models.CheckConstraint(condition=models.Q(discount_amount__gte=0), name='salesitem_discount_amount_gte_0'),
            models.CheckConstraint(condition=models.Q(taxable_amount__gte=0), name='salesitem_taxable_amount_gte_0'),
            models.CheckConstraint(condition=models.Q(gst_percentage__gte=0), name='salesitem_gst_percentage_gte_0'),
            models.CheckConstraint(condition=models.Q(gst_amount__gte=0), name='salesitem_gst_amount_gte_0'),
            models.CheckConstraint(condition=models.Q(line_total__gte=0), name='salesitem_line_total_gte_0'),
        ]

    def __str__(self):
        return f"{self.sales.sales_number} - {self.material.material_name}"
