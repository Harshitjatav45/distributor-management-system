from django.utils import timezone
from rest_framework.exceptions import ValidationError
from sales.models import Sales
from dispatch.models import Dispatch

VALID_TRANSITIONS = {
    'DISPATCHED': {'OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED', 'CANCELLED'},
    'OUT_FOR_DELIVERY': {'DELIVERED', 'FAILED', 'CANCELLED'},
    'FAILED': {'OUT_FOR_DELIVERY', 'CANCELLED'},
    'DELIVERED': set(),
    'CANCELLED': set(),
}


def create_dispatch(serializer):
    """Locks the Sales row, verifies it's CONFIRMED with no active Dispatch,
    then saves. Caller must wrap this in transaction.atomic() (done in the
    view's perform_create).
    """
    sales_id = serializer.validated_data['sales'].id
    sales = Sales.objects.select_for_update().get(pk=sales_id)

    if sales.status != 'CONFIRMED':
        raise ValidationError({
            'sales': (
                f"Cannot dispatch sales '{sales.sales_number}': status is {sales.status}, "
                f"only CONFIRMED sales orders can be dispatched."
            )
        })

    has_active_dispatch = Dispatch.objects.filter(sales=sales).exclude(status='CANCELLED').exists()
    if has_active_dispatch:
        raise ValidationError({
            'sales': (
                f"Sales '{sales.sales_number}' already has an active Dispatch. "
                f"Cancel it before creating a new one."
            )
        })

    return serializer.save()


def apply_dispatch_status_change(dispatch, new_status):
    """Applies side effects of a Dispatch status transition. Caller must have
    already locked `dispatch`, validated the transition is legal, and saved
    the new status before calling this.
    """
    if new_status == 'DELIVERED' and dispatch.actual_delivery_date is None:
        dispatch.actual_delivery_date = timezone.now().date()
        dispatch.save()
