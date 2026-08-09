from django.db import transaction
from rest_framework import generics
from rest_framework.exceptions import ValidationError, PermissionDenied
from purchase.models import Purchase, PurchaseItem
from purchase.serializers import PurchaseSerializer, PurchaseItemSerializer
from purchase.services import confirm_purchase, cancel_purchase
from accounts.permissions import DenyDeleteUnlessAdmin, is_admin_or_manager


class PurchaseListCreateAPIView(generics.ListCreateAPIView):
    queryset = Purchase.objects.all().order_by("-purchase_date", "-id")
    serializer_class = PurchaseSerializer


class PurchaseRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Purchase.objects.all().order_by("-purchase_date", "-id")
    serializer_class = PurchaseSerializer
    permission_classes = [DenyDeleteUnlessAdmin]

    def perform_update(self, serializer):
        with transaction.atomic():
            locked_purchase = Purchase.objects.select_for_update().get(pk=serializer.instance.pk)
            old_status = locked_purchase.status
            new_status = serializer.validated_data.get('status', old_status)

            # Confirming, or cancelling an already-CONFIRMED Purchase, is a
            # financial action (triggers Stock + Ledger automation) - only
            # Admin/Manager may do it. Staff can still freely edit or even
            # void a DRAFT (DRAFT -> CANCELLED has no financial effect and
            # is left open, same as deleting a draft item already is).
            # Placed here, next to the existing status comparison, rather
            # than as a separate permission class, since it depends on the
            # specific old/new status of this request, not just "can this
            # user touch Purchase at all".
            is_sensitive_transition = (
                (old_status == 'DRAFT' and new_status == 'CONFIRMED')
                or (old_status == 'CONFIRMED' and new_status == 'CANCELLED')
            )
            if is_sensitive_transition and not is_admin_or_manager(self.request.user):
                raise PermissionDenied(
                    "Only Admin or Manager can confirm or cancel a Purchase."
                )

            serializer.save()

            if old_status != new_status:
                if old_status == 'DRAFT' and new_status == 'CONFIRMED':
                    confirm_purchase(serializer.instance)
                elif old_status == 'CONFIRMED' and new_status == 'CANCELLED':
                    cancel_purchase(serializer.instance)


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
