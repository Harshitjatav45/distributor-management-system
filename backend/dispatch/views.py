from django.db import transaction
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from dispatch.models import Dispatch
from dispatch.serializers import DispatchSerializer
from dispatch.services import create_dispatch, apply_dispatch_status_change
from audit.services import write_audit


class DispatchListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = DispatchSerializer
    search_fields = ['dispatch_number', 'sales__sales_number']

    def get_queryset(self):
        # See PurchaseListCreateAPIView.get_queryset() for why this exists.
        queryset = Dispatch.objects.all().order_by("-dispatch_date", "-id")
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def perform_create(self, serializer):
        with transaction.atomic():
            dispatch = create_dispatch(serializer)
            write_audit(
                actor=self.request.user, action='CREATE', model_name='Dispatch',
                object_id=dispatch.id, object_repr=dispatch.dispatch_number,
                after={'status': dispatch.status, 'sales_id': dispatch.sales_id},
            )


class DispatchRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Dispatch.objects.all().order_by("-dispatch_date", "-id")
    serializer_class = DispatchSerializer

    def perform_update(self, serializer):
        with transaction.atomic():
            locked_dispatch = Dispatch.objects.select_for_update().get(pk=serializer.instance.pk)
            old_status = locked_dispatch.status
            new_status = serializer.validated_data.get('status', old_status)

            serializer.save()

            if old_status != new_status:
                apply_dispatch_status_change(serializer.instance, new_status)
                write_audit(
                    actor=self.request.user,
                    action='CANCEL' if new_status == 'CANCELLED' else 'STATUS_CHANGE',
                    model_name='Dispatch', object_id=serializer.instance.id,
                    object_repr=serializer.instance.dispatch_number,
                    before={'status': old_status}, after={'status': new_status},
                )

    def perform_destroy(self, instance):
        raise ValidationError(
            "Dispatch records cannot be deleted. Cancel the dispatch instead to preserve tracking history."
        )


class DispatchBySalesAPIView(APIView):
    def get(self, request, sales_id):
        dispatches = Dispatch.objects.filter(sales_id=sales_id).order_by('-id')
        serializer = DispatchSerializer(dispatches, many=True)
        return Response(serializer.data)
