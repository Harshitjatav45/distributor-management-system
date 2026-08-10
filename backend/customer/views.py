from rest_framework import generics
from customer.models import Customer
from customer.serializers import CustomerSerializer
from accounts.permissions import DenyDeleteUnlessAdmin
from audit.mixins import AuditedMasterDataMixin


class CustomerListCreateAPIView(AuditedMasterDataMixin, generics.ListCreateAPIView):
    queryset = Customer.objects.all().order_by("customer_name")
    serializer_class = CustomerSerializer
    permission_classes = [DenyDeleteUnlessAdmin]
    audit_repr_field = 'customer_name'


class CustomerRetrieveUpdateDestroyAPIView(AuditedMasterDataMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all().order_by("customer_name")
    serializer_class = CustomerSerializer
    permission_classes = [DenyDeleteUnlessAdmin]
    audit_repr_field = 'customer_name'
