from rest_framework import generics
from purchase.models import Purchase, PurchaseItem
from purchase.serializers import PurchaseSerializer, PurchaseItemSerializer


class PurchaseListCreateAPIView(generics.ListCreateAPIView):
    queryset = Purchase.objects.all().order_by("-purchase_date", "-id")
    serializer_class = PurchaseSerializer


class PurchaseRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Purchase.objects.all().order_by("-purchase_date", "-id")
    serializer_class = PurchaseSerializer


class PurchaseItemListCreateAPIView(generics.ListCreateAPIView):
    queryset = PurchaseItem.objects.all().order_by("-id")
    serializer_class = PurchaseItemSerializer


class PurchaseItemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseItem.objects.all().order_by("-id")
    serializer_class = PurchaseItemSerializer
