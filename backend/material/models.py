from django.core.validators import MinValueValidator
from django.db import models
from company.models import Company
from category.models import Category


class Material(models.Model):
    UNIT_CHOICES = [
        ('PCS', 'Pieces'),
        ('KG', 'Kilogram'),
        ('TON', 'Ton'),
        ('METER', 'Meter'),
        ('FEET', 'Feet'),
        ('BUNDLE', 'Bundle'),
        ('NOS', 'Numbers'),
        ('BOX', 'Box'),
        ('SET', 'Set'),
        ('PKT', 'Packet'),
    ]

    material_name = models.CharField(max_length=255)
    material_code = models.CharField(max_length=50, unique=True)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='materials')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='materials')
    brand = models.CharField(max_length=100, blank=True, null=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=100, blank=True, null=True)
    hsn_code = models.CharField(max_length=20, blank=True, null=True)
    unit = models.CharField(max_length=50, choices=UNIT_CHOICES, default='PCS', blank=True, null=True)
    weight_per_unit = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True, validators=[MinValueValidator(0)])
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    minimum_stock_level = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, validators=[MinValueValidator(0)])
    mrp = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Database-level enforcement (unlike MinValueValidator, which only
        # runs on full_clean()/ModelForm validation, not on a raw .save())-
        # this is the actual defense-in-depth layer against a direct ORM
        # write or raw SQL bypassing the serializer validation above it.
        constraints = [
            models.CheckConstraint(condition=models.Q(mrp__gte=0), name='material_mrp_gte_0'),
            models.CheckConstraint(condition=models.Q(purchase_price__gte=0), name='material_purchase_price_gte_0'),
            models.CheckConstraint(condition=models.Q(selling_price__gte=0), name='material_selling_price_gte_0'),
            models.CheckConstraint(condition=models.Q(gst_percentage__gte=0), name='material_gst_percentage_gte_0'),
            models.CheckConstraint(condition=models.Q(minimum_stock_level__gte=0), name='material_minimum_stock_level_gte_0'),
            models.CheckConstraint(
                condition=models.Q(weight_per_unit__isnull=True) | models.Q(weight_per_unit__gte=0),
                name='material_weight_per_unit_gte_0',
            ),
        ]

    def __str__(self):
        return f"{self.material_name} ({self.material_code})"
