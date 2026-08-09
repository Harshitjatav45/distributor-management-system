from django.db import transaction
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from payment.models import Payment
from payment.serializers import PaymentSerializer
from payment.services import (
    lock_and_validate_payment_in,
    lock_and_validate_payment_out,
    post_payment_in_ledger_entry,
    post_payment_out_ledger_entry,
    cancel_payment,
)


class PaymentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Payment.objects.all().order_by("-payment_date", "-id")
    serializer_class = PaymentSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            payment_type = serializer.validated_data['payment_type']
            amount = serializer.validated_data['amount']

            if payment_type == 'PAYMENT_IN':
                customer_id = serializer.validated_data['customer'].id
                customer, new_balance = lock_and_validate_payment_in(customer_id, amount)
                payment = serializer.save()
                post_payment_in_ledger_entry(payment, customer, new_balance)
            else:
                supplier_id = serializer.validated_data['supplier'].id
                supplier, new_balance = lock_and_validate_payment_out(supplier_id, amount)
                payment = serializer.save()
                post_payment_out_ledger_entry(payment, supplier, new_balance)


class PaymentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Payment.objects.all().order_by("-payment_date", "-id")
    serializer_class = PaymentSerializer

    def perform_update(self, serializer):
        with transaction.atomic():
            locked_payment = Payment.objects.select_for_update().get(pk=serializer.instance.pk)
            old_status = locked_payment.status
            new_status = serializer.validated_data.get('status', old_status)

            serializer.save()

            if old_status != new_status and old_status == 'CONFIRMED' and new_status == 'CANCELLED':
                cancel_payment(serializer.instance)

    def perform_destroy(self, instance):
        raise ValidationError(
            "Payments cannot be deleted. Cancel the payment instead to preserve the Ledger audit trail."
        )
