from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, F, Value, DecimalField, OuterRef, Subquery
from django.db.models.functions import Coalesce

from purchase.models import Purchase, PurchaseItem
from sales.models import Sales, SalesItem
from stock.models import Stock
from customer.models import Customer
from supplier.models import Supplier
from ledger.models import Ledger
from accounts.permissions import IsAdminOrManager


class PurchaseReportAPIView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        data = PurchaseItem.objects.select_related(
            'purchase', 'purchase__supplier', 'material'
        ).values(
            'purchase__purchase_number',
            'purchase__purchase_date',
            'purchase__supplier__supplier_name',
            'purchase__invoice_number',
            'purchase__invoice_date',
            'purchase__status',
            'purchase__payment_status',
            'purchase__grand_total',
            'material__material_name',
            'quantity',
            'unit',
            'rate',
            'gst_percentage',
            'line_total',
        )
        return Response(list(data))


class SalesReportAPIView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        data = SalesItem.objects.select_related(
            'sales', 'sales__customer', 'material'
        ).values(
            'sales__sales_number',
            'sales__sales_date',
            'sales__customer__customer_name',
            'sales__invoice_number',
            'sales__invoice_date',
            'sales__status',
            'sales__payment_status',
            'sales__grand_total',
            'material__material_name',
            'quantity',
            'unit',
            'rate',
            'gst_percentage',
            'line_total',
        )
        return Response(list(data))


class StockReportAPIView(APIView):
    def get(self, request):
        data = Stock.objects.select_related('material').values(
            'material__material_name',
            'material__material_code',
            'material__category__category_name',
            'material__unit',
            'material__minimum_stock_level',
            'current_stock',
            'reserved_stock',
            'available_stock',
            'last_purchase_price',
            'average_purchase_price',
            'is_active',
        )
        return Response(list(data))


class CustomerReportAPIView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        sales_subquery = Sales.objects.filter(
            customer=OuterRef('pk')
        ).order_by().values('customer').annotate(
            total=Sum('grand_total')
        ).values('total')

        debit_subquery = Ledger.objects.filter(
            customer=OuterRef('pk'), entry_type='DEBIT'
        ).order_by().values('customer').annotate(
            total=Sum('amount')
        ).values('total')

        credit_subquery = Ledger.objects.filter(
            customer=OuterRef('pk'), entry_type='CREDIT'
        ).order_by().values('customer').annotate(
            total=Sum('amount')
        ).values('total')

        data = Customer.objects.annotate(
            total_sales_amount=Coalesce(
                Subquery(sales_subquery, output_field=DecimalField()), Value(0), output_field=DecimalField()
            ),
            total_debit=Coalesce(
                Subquery(debit_subquery, output_field=DecimalField()), Value(0), output_field=DecimalField()
            ),
            total_credit=Coalesce(
                Subquery(credit_subquery, output_field=DecimalField()), Value(0), output_field=DecimalField()
            ),
        ).annotate(
            outstanding_balance=F('total_debit') - F('total_credit')
        ).values(
            'id',
            'customer_name',
            'customer_code',
            'customer_type',
            'city',
            'state',
            'mobile_number',
            'credit_limit',
            'credit_days',
            'is_active',
            'total_sales_amount',
            'outstanding_balance',
        )
        return Response(list(data))


class SupplierReportAPIView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        purchase_subquery = Purchase.objects.filter(
            supplier=OuterRef('pk')
        ).order_by().values('supplier').annotate(
            total=Sum('grand_total')
        ).values('total')

        debit_subquery = Ledger.objects.filter(
            supplier=OuterRef('pk'), entry_type='DEBIT'
        ).order_by().values('supplier').annotate(
            total=Sum('amount')
        ).values('total')

        credit_subquery = Ledger.objects.filter(
            supplier=OuterRef('pk'), entry_type='CREDIT'
        ).order_by().values('supplier').annotate(
            total=Sum('amount')
        ).values('total')

        data = Supplier.objects.annotate(
            total_purchase_amount=Coalesce(
                Subquery(purchase_subquery, output_field=DecimalField()), Value(0), output_field=DecimalField()
            ),
            total_debit=Coalesce(
                Subquery(debit_subquery, output_field=DecimalField()), Value(0), output_field=DecimalField()
            ),
            total_credit=Coalesce(
                Subquery(credit_subquery, output_field=DecimalField()), Value(0), output_field=DecimalField()
            ),
        ).annotate(
            outstanding_balance=F('total_credit') - F('total_debit')
        ).values(
            'id',
            'supplier_name',
            'supplier_code',
            'supplier_type',
            'city',
            'state',
            'mobile_number',
            'credit_limit',
            'credit_days',
            'is_active',
            'total_purchase_amount',
            'outstanding_balance',
        )
        return Response(list(data))


class LedgerReportAPIView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        data = Ledger.objects.select_related('customer', 'supplier').annotate(
            party_name=Coalesce('customer__customer_name', 'supplier__supplier_name')
        ).values(
            'transaction_date',
            'reference_type',
            'reference_id',
            'party_name',
            'entry_type',
            'amount',
            'balance',
            'remarks',
        )
        return Response(list(data))
