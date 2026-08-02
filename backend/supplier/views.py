from rest_framework import generics
from supplier.models import Supplier
from supplier.serializers import SupplierSerializer


class SupplierListCreateAPIView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all().order_by("supplier_name")
    serializer_class = SupplierSerializer


class SupplierRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Supplier.objects.all().order_by("supplier_name")
    serializer_class = SupplierSerializer
