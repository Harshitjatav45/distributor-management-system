from rest_framework import generics
from stock.models import Stock
from stock.serializers import StockSerializer
from accounts.permissions import StockPermission


class StockListCreateAPIView(generics.ListCreateAPIView):
    queryset = Stock.objects.all().order_by("material__material_name")
    serializer_class = StockSerializer
    permission_classes = [StockPermission]


class StockRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Stock.objects.all().order_by("material__material_name")
    serializer_class = StockSerializer
    permission_classes = [StockPermission]
