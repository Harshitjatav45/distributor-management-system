from django.db import transaction
from rest_framework import generics
from stock.models import Stock
from stock.serializers import StockSerializer
from accounts.permissions import StockPermission
from audit.services import write_audit


class StockListCreateAPIView(generics.ListCreateAPIView):
    queryset = Stock.objects.all().order_by("material__material_name")
    serializer_class = StockSerializer
    permission_classes = [StockPermission]
    search_fields = ['material__material_name', 'material__material_code']


class StockRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Stock.objects.all().order_by("material__material_name")
    serializer_class = StockSerializer
    permission_classes = [StockPermission]

    def perform_update(self, serializer):
        # Stock writes are Admin/Manager-only manual corrections (see
        # StockPermission) - exactly the kind of action that needs an audit
        # trail, since it directly overrides inventory numbers that are
        # otherwise only ever changed automatically by Purchase/Sales.
        with transaction.atomic():
            before = self.get_serializer(serializer.instance).data
            instance = serializer.save()
            write_audit(
                actor=self.request.user,
                action='UPDATE',
                model_name='Stock',
                object_id=instance.pk,
                object_repr=instance.material.material_name,
                before=before,
                after=serializer.data,
            )

    def perform_destroy(self, instance):
        with transaction.atomic():
            object_repr = instance.material.material_name
            before = self.get_serializer(instance).data
            instance.delete()
            write_audit(
                actor=self.request.user,
                action='DELETE',
                model_name='Stock',
                object_id=instance.pk,
                object_repr=object_repr,
                before=before,
            )
