from rest_framework import generics
from supplier.models import Supplier
from supplier.serializers import SupplierSerializer
from accounts.permissions import DenyDeleteUnlessAdmin
from audit.mixins import AuditedMasterDataMixin


class SupplierListCreateAPIView(AuditedMasterDataMixin, generics.ListCreateAPIView):
    queryset = Supplier.objects.all().order_by("supplier_name")
    serializer_class = SupplierSerializer
    permission_classes = [DenyDeleteUnlessAdmin]
    audit_repr_field = 'supplier_name'
    search_fields = ['supplier_name', 'supplier_code']


class SupplierRetrieveUpdateDestroyAPIView(AuditedMasterDataMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Supplier.objects.all().order_by("supplier_name")
    serializer_class = SupplierSerializer
    permission_classes = [DenyDeleteUnlessAdmin]
    audit_repr_field = 'supplier_name'
