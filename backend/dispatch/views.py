from django.db import transaction
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from dispatch.models import Dispatch
from dispatch.serializers import DispatchSerializer
from dispatch.services import create_dispatch, apply_dispatch_status_change


class DispatchListCreateAPIView(generics.ListCreateAPIView):
    queryset = Dispatch.objects.all().order_by("-dispatch_date", "-id")
    serializer_class = DispatchSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            create_dispatch(serializer)


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

    def perform_destroy(self, instance):
        raise ValidationError(
            "Dispatch records cannot be deleted. Cancel the dispatch instead to preserve tracking history."
        )


class DispatchBySalesAPIView(APIView):
    def get(self, request, sales_id):
        dispatches = Dispatch.objects.filter(sales_id=sales_id).order_by('-id')
        serializer = DispatchSerializer(dispatches, many=True)
        return Response(serializer.data)
