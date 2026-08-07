from rest_framework import generics
from sales.models import Sales, SalesItem
from sales.serializers import SalesSerializer, SalesItemSerializer


class SalesListCreateAPIView(generics.ListCreateAPIView):
    queryset = Sales.objects.all().order_by("-sales_date", "-id")
    serializer_class = SalesSerializer


class SalesRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sales.objects.all().order_by("-sales_date", "-id")
    serializer_class = SalesSerializer


class SalesItemListCreateAPIView(generics.ListCreateAPIView):
    queryset = SalesItem.objects.all().order_by("-id")
    serializer_class = SalesItemSerializer


class SalesItemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SalesItem.objects.all().order_by("-id")
    serializer_class = SalesItemSerializer
