from django.db import transaction
from rest_framework import generics
from rest_framework.exceptions import ValidationError, PermissionDenied
from sales.models import Sales, SalesItem
from sales.serializers import SalesSerializer, SalesItemSerializer
from sales.services import confirm_sales, cancel_sales
from accounts.permissions import DenyDeleteUnlessAdmin, is_admin_or_manager
from audit.services import write_audit


class SalesListCreateAPIView(generics.ListCreateAPIView):
    queryset = Sales.objects.all().order_by("-sales_date", "-id")
    serializer_class = SalesSerializer


class SalesRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sales.objects.all().order_by("-sales_date", "-id")
    serializer_class = SalesSerializer
    permission_classes = [DenyDeleteUnlessAdmin]

    def perform_update(self, serializer):
        with transaction.atomic():
            locked_sales = Sales.objects.select_for_update().get(pk=serializer.instance.pk)
            old_status = locked_sales.status
            new_status = serializer.validated_data.get('status', old_status)

            # Same reasoning as Purchase: confirming, or cancelling an
            # already-CONFIRMED Sales, is a financial action reserved for
            # Admin/Manager. DRAFT -> CANCELLED (voiding a draft) stays open
            # to Staff since it has no Stock/Ledger effect.
            is_sensitive_transition = (
                (old_status == 'DRAFT' and new_status == 'CONFIRMED')
                or (old_status == 'CONFIRMED' and new_status == 'CANCELLED')
            )
            if is_sensitive_transition and not is_admin_or_manager(self.request.user):
                raise PermissionDenied(
                    "Only Admin or Manager can confirm or cancel a Sales order."
                )

            serializer.save()

            if old_status != new_status:
                if old_status == 'DRAFT' and new_status == 'CONFIRMED':
                    confirm_sales(serializer.instance)
                    write_audit(
                        actor=self.request.user, action='CONFIRM', model_name='Sales',
                        object_id=serializer.instance.id, object_repr=serializer.instance.sales_number,
                        before={'status': old_status},
                        after={'status': new_status, 'grand_total': str(serializer.instance.grand_total)},
                    )
                elif old_status == 'CONFIRMED' and new_status == 'CANCELLED':
                    cancel_sales(serializer.instance)
                    write_audit(
                        actor=self.request.user, action='CANCEL', model_name='Sales',
                        object_id=serializer.instance.id, object_repr=serializer.instance.sales_number,
                        before={'status': old_status},
                        after={'status': new_status, 'grand_total': str(serializer.instance.grand_total)},
                    )


class SalesItemListCreateAPIView(generics.ListCreateAPIView):
    queryset = SalesItem.objects.all().order_by("-id")
    serializer_class = SalesItemSerializer


class SalesItemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SalesItem.objects.all().order_by("-id")
    serializer_class = SalesItemSerializer

    def perform_destroy(self, instance):
        if instance.sales.status != 'DRAFT':
            raise ValidationError(
                "Cannot delete items from a sales order that is not in DRAFT status."
            )
        instance.delete()
