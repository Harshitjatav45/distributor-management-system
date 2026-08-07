from django.urls import path
from reports.views import (
    PurchaseReportAPIView,
    SalesReportAPIView,
    StockReportAPIView,
    CustomerReportAPIView,
    SupplierReportAPIView,
    LedgerReportAPIView,
)

urlpatterns = [
    path('purchase/', PurchaseReportAPIView.as_view(), name='report-purchase'),
    path('sales/', SalesReportAPIView.as_view(), name='report-sales'),
    path('stock/', StockReportAPIView.as_view(), name='report-stock'),
    path('customers/', CustomerReportAPIView.as_view(), name='report-customers'),
    path('suppliers/', SupplierReportAPIView.as_view(), name='report-suppliers'),
    path('ledger/', LedgerReportAPIView.as_view(), name='report-ledger'),
]
