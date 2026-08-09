from django.db import transaction
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from purchase.models import Purchase, PurchaseItem
from purchase.serializers import PurchaseSerializer, PurchaseItemSerializer
from purchase.services import apply_purchase_confirmation, reverse_purchase_confirmation


class PurchaseListCreateAPIView(generics.ListCreateAPIView):
    queryset = Purchase.objects.all().order_by("-purchase_date", "-id")
    serializer_class = PurchaseSerializer


class PurchaseRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Purchase.objects.all().order_by("-purchase_date", "-id")
    serializer_class = PurchaseSerializer

    def perform_update(self, serializer):
        with transaction.atomic():
            locked_purchase = Purchase.objects.select_for_update().get(pk=serializer.instance.pk)
            old_status = locked_purchase.status
            new_status = serializer.validated_data.get('status', old_status)

            serializer.save()

            if old_status != new_status:
                if old_status == 'DRAFT' and new_status == 'CONFIRMED':
                    apply_purchase_confirmation(serializer.instance)
                elif old_status == 'CONFIRMED' and new_status == 'CANCELLED':
                    reverse_purchase_confirmation(serializer.instance)


class PurchaseItemListCreateAPIView(generics.ListCreateAPIView):
    queryset = PurchaseItem.objects.all().order_by("-id")
    serializer_class = PurchaseItemSerializer


class PurchaseItemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseItem.objects.all().order_by("-id")
    serializer_class = PurchaseItemSerializer

    def perform_destroy(self, instance):
        if instance.purchase.status != 'DRAFT':
            raise ValidationError(
                "Cannot delete items from a purchase that is not in DRAFT status."
            )
        instance.delete()
