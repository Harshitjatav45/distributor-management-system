from django.db import models
from customer.models import Customer
from supplier.models import Supplier


class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('PAYMENT_IN', 'Payment In'),
        ('PAYMENT_OUT', 'Payment Out'),
    ]

    PAYMENT_MODE_CHOICES = [
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('UPI', 'UPI'),
        ('OTHER', 'Other'),
    ]

    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    ]

    payment_number = models.CharField(max_length=50, unique=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    payment_date = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, blank=True, null=True, related_name='payments')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, blank=True, null=True, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, blank=True, null=True)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.payment_number} ({self.payment_type})"
