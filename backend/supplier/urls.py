from django.urls import path
from supplier.views import SupplierListCreateAPIView, SupplierRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('', SupplierListCreateAPIView.as_view(), name='supplier-list-create'),
    path('<int:pk>/', SupplierRetrieveUpdateDestroyAPIView.as_view(), name='supplier-detail'),
]
