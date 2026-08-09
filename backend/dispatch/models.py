from django.db import models
from sales.models import Sales


class Dispatch(models.Model):
    STATUS_CHOICES = [
        ('DISPATCHED', 'Dispatched'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    dispatch_number = models.CharField(max_length=50, unique=True)
    sales = models.ForeignKey(Sales, on_delete=models.PROTECT, related_name='dispatches')
    dispatch_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DISPATCHED')
    transport_name = models.CharField(max_length=255, blank=True, null=True)
    vehicle_number = models.CharField(max_length=20, blank=True, null=True)
    lr_number = models.CharField(max_length=50, blank=True, null=True)
    delivery_person = models.CharField(max_length=255, blank=True, null=True)
    delivery_address = models.TextField(blank=True, null=True)
    expected_delivery_date = models.DateField(blank=True, null=True)
    actual_delivery_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.dispatch_number} ({self.sales.sales_number})"
