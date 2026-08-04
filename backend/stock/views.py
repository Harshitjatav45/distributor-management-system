from rest_framework import generics
from stock.models import Stock
from stock.serializers import StockSerializer


class StockListCreateAPIView(generics.ListCreateAPIView):
    queryset = Stock.objects.all().order_by("material__material_name")
    serializer_class = StockSerializer


class StockRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Stock.objects.all().order_by("material__material_name")
    serializer_class = StockSerializer
