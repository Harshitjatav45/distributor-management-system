import logging
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
from accounts.permissions import IsAdminOrManager
from audit.services import write_audit

logger = logging.getLogger(__name__)


class PaymentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Payment.objects.all().order_by("-payment_date", "-id")
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrManager]

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

            write_audit(
                actor=self.request.user, action='CREATE', model_name='Payment',
                object_id=payment.id, object_repr=payment.payment_number,
                after={'payment_type': payment.payment_type, 'amount': str(payment.amount), 'status': payment.status},
            )

            logger.info(
                "Payment created: payment_number=%s payment_type=%s",
                payment.payment_number, payment.payment_type,
            )


class PaymentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Payment.objects.all().order_by("-payment_date", "-id")
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrManager]

    def perform_update(self, serializer):
        with transaction.atomic():
            locked_payment = Payment.objects.select_for_update().get(pk=serializer.instance.pk)
            old_status = locked_payment.status
            new_status = serializer.validated_data.get('status', old_status)

            serializer.save()

            if old_status != new_status and old_status == 'CONFIRMED' and new_status == 'CANCELLED':
                cancel_payment(serializer.instance)
                write_audit(
                    actor=self.request.user, action='CANCEL', model_name='Payment',
                    object_id=serializer.instance.id, object_repr=serializer.instance.payment_number,
                    before={'status': old_status}, after={'status': new_status},
                )

    def perform_destroy(self, instance):
        raise ValidationError(
            "Payments cannot be deleted. Cancel the payment instead to preserve the Ledger audit trail."
        )
