from django.db import transaction
from rest_framework import generics
from rest_framework.exceptions import ValidationError, PermissionDenied
from purchase.models import Purchase, PurchaseItem
from purchase.serializers import PurchaseSerializer, PurchaseItemSerializer
from purchase.services import confirm_purchase, cancel_purchase
from accounts.permissions import DenyDeleteUnlessAdmin, is_admin_or_manager
from audit.services import write_audit


class PurchaseListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PurchaseSerializer
    search_fields = ['purchase_number', 'supplier__supplier_name']

    def get_queryset(self):
        # ?status=DRAFT|CONFIRMED|CANCELLED - lets a caller get an exact
        # status-scoped count (via page_size=1 + the count envelope field)
        # without fetching every row, and lets the frontend's status
        # dropdown filter server-side instead of only within one page.
        queryset = Purchase.objects.all().order_by("-purchase_date", "-id")
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


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
                    write_audit(
                        actor=self.request.user, action='CONFIRM', model_name='Purchase',
                        object_id=serializer.instance.id, object_repr=serializer.instance.purchase_number,
                        before={'status': old_status},
                        after={'status': new_status, 'grand_total': str(serializer.instance.grand_total)},
                    )
                elif old_status == 'CONFIRMED' and new_status == 'CANCELLED':
                    cancel_purchase(serializer.instance)
                    write_audit(
                        actor=self.request.user, action='CANCEL', model_name='Purchase',
                        object_id=serializer.instance.id, object_repr=serializer.instance.purchase_number,
                        before={'status': old_status},
                        after={'status': new_status, 'grand_total': str(serializer.instance.grand_total)},
                    )


def _purchase_item_repr(item):
    return f"{item.purchase.purchase_number} - {item.material.material_name}"


class PurchaseItemListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PurchaseItemSerializer

    def get_queryset(self):
        # Supports ?purchase=<id> so a client can fetch just one Purchase's
        # items directly - needed now that this list is paginated (fetching
        # every PurchaseItem in the system and filtering client-side, as
        # the frontend previously did, would silently drop a purchase's
        # items once they fall past page 1).
        queryset = PurchaseItem.objects.all().order_by("-id")
        purchase_id = self.request.query_params.get('purchase')
        if purchase_id:
            queryset = queryset.filter(purchase_id=purchase_id)
        return queryset

    def perform_create(self, serializer):
        with transaction.atomic():
            item = serializer.save()
            write_audit(
                actor=self.request.user, action='CREATE', model_name='PurchaseItem',
                object_id=item.id, object_repr=_purchase_item_repr(item), after=serializer.data,
            )


class PurchaseItemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseItem.objects.all().order_by("-id")
    serializer_class = PurchaseItemSerializer

    def perform_update(self, serializer):
        with transaction.atomic():
            before = self.get_serializer(serializer.instance).data
            item = serializer.save()
            write_audit(
                actor=self.request.user, action='UPDATE', model_name='PurchaseItem',
                object_id=item.id, object_repr=_purchase_item_repr(item),
                before=before, after=serializer.data,
            )

    def perform_destroy(self, instance):
        if instance.purchase.status != 'DRAFT':
            raise ValidationError(
                "Cannot delete items from a purchase that is not in DRAFT status."
            )
        with transaction.atomic():
            object_repr = _purchase_item_repr(instance)
            before = self.get_serializer(instance).data
            instance.delete()
            write_audit(
                actor=self.request.user, action='DELETE', model_name='PurchaseItem',
                object_id=before['id'], object_repr=object_repr, before=before,
            )
