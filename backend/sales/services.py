from decimal import Decimal
from django.db.models import Sum
from rest_framework.exceptions import ValidationError
from stock.models import Stock


def _materials_with_quantity(sales):
    """Aggregate quantity per material across this Sales' line items, in a
    deterministic ascending material_id order (required for deadlock-free
    Stock row locking). Aggregating first means a material appearing on more
    than one line within the same Sales is only locked/updated once, with the
    combined quantity - not once per line.
    """
    return list(
        sales.items.values('material_id', 'material__material_name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('material_id')
    )


def deduct_sales_stock(sales):
    """Deduct stock for every SalesItem on a Sales moving DRAFT -> CONFIRMED.

    Two-pass: validate every material's availability first (locking each
    Stock row along the way), only then apply any deduction. A shortage on
    any single material rejects the whole confirmation with none deducted.
    """
    lines = _materials_with_quantity(sales)

    locked_stocks = {}
    for line in lines:
        material_id = line['material_id']
        required = line['total_quantity']
        stock = Stock.objects.select_for_update().filter(material_id=material_id).first()
        available = stock.available_stock if stock is not None else Decimal('0')

        if stock is None or available < required:
            shortage = required - available
            raise ValidationError({
                'items': (
                    f"Insufficient stock for '{line['material__material_name']}': "
                    f"available {available}, required {required}, short by {shortage}."
                )
            })
        locked_stocks[material_id] = stock

    for line in lines:
        stock = locked_stocks[line['material_id']]
        stock.current_stock = stock.current_stock - line['total_quantity']
        stock.available_stock = stock.available_stock - line['total_quantity']
        stock.save()


def restore_sales_stock(sales):
    """Restore stock for every SalesItem on a Sales moving CONFIRMED -> CANCELLED.

    Restoring (adding back) can never itself produce a negative result, so
    unlike a Purchase reversal this needs no "would go negative" guard.
    """
    lines = _materials_with_quantity(sales)

    locked_stocks = {}
    for line in lines:
        material_id = line['material_id']
        stock = Stock.objects.select_for_update().get(material_id=material_id)
        locked_stocks[material_id] = stock

    for line in lines:
        stock = locked_stocks[line['material_id']]
        stock.current_stock = stock.current_stock + line['total_quantity']
        stock.available_stock = stock.available_stock + line['total_quantity']
        stock.save()


def confirm_sales(sales):
    """Orchestrates DRAFT -> CONFIRMED."""
    deduct_sales_stock(sales)


def cancel_sales(sales):
    """Orchestrates CONFIRMED -> CANCELLED."""
    restore_sales_stock(sales)
