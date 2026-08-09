from rest_framework import generics
from customer.models import Customer
from customer.serializers import CustomerSerializer
from accounts.permissions import DenyDeleteUnlessAdmin


class CustomerListCreateAPIView(generics.ListCreateAPIView):
    queryset = Customer.objects.all().order_by("customer_name")
    serializer_class = CustomerSerializer
    permission_classes = [DenyDeleteUnlessAdmin]


class CustomerRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all().order_by("customer_name")
    serializer_class = CustomerSerializer
    permission_classes = [DenyDeleteUnlessAdmin]
