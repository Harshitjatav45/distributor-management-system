from decimal import Decimal
from rest_framework.exceptions import ValidationError
from stock.models import Stock


def _effective_quantity(item):
    return item.received_quantity if item.received_quantity is not None else item.quantity


def apply_purchase_confirmation(purchase):
    """Increase stock for every item on a Purchase moving DRAFT -> CONFIRMED."""
    for item in purchase.items.select_related('material').all():
        qty = _effective_quantity(item)
        stock, _ = Stock.objects.select_for_update().get_or_create(material=item.material)

        old_qty = stock.current_stock
        old_average = stock.average_purchase_price or Decimal('0')
        new_qty = old_qty + qty

        if new_qty > 0:
            new_average = ((old_average * old_qty) + (item.rate * qty)) / new_qty
        else:
            new_average = item.rate

        stock.current_stock = new_qty
        stock.available_stock = stock.available_stock + qty
        stock.last_purchase_price = item.rate
        stock.average_purchase_price = new_average
        stock.save()


def reverse_purchase_confirmation(purchase):
    """Reverse stock for every item on a Purchase moving CONFIRMED -> CANCELLED.

    average_purchase_price / last_purchase_price are intentionally NOT reversed here:
    correctly undoing a moving weighted average requires a movement history
    (a future StockMovement ledger), which this implementation does not add.
    Only current_stock / available_stock are reversed.
    """
    items = list(purchase.items.select_related('material').all())

    # First pass: validate the reversal won't drive any material negative.
    for item in items:
        qty = _effective_quantity(item)
        stock = Stock.objects.select_for_update().filter(material=item.material).first()
        if stock is None:
            raise ValidationError({
                'status': f"Cannot cancel: no stock record found for '{item.material.material_name}'."
            })
        if stock.current_stock - qty < 0 or stock.available_stock - qty < 0:
            raise ValidationError({
                'status': (
                    f"Cannot cancel: reversing this purchase would make stock for "
                    f"'{item.material.material_name}' negative "
                    f"(current: {stock.current_stock}, available: {stock.available_stock}, "
                    f"reversal amount: {qty})."
                )
            })

    # Second pass: apply the reversal now that every line has been validated.
    for item in items:
        qty = _effective_quantity(item)
        stock = Stock.objects.select_for_update().get(material=item.material)
        stock.current_stock = stock.current_stock - qty
        stock.available_stock = stock.available_stock - qty
        stock.save()
