from django.urls import path
from purchase.views import (
    PurchaseListCreateAPIView,
    PurchaseRetrieveUpdateDestroyAPIView,
    PurchaseItemListCreateAPIView,
    PurchaseItemRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path('', PurchaseListCreateAPIView.as_view(), name='purchase-list-create'),
    path('<int:pk>/', PurchaseRetrieveUpdateDestroyAPIView.as_view(), name='purchase-detail'),

    path('purchase-items/', PurchaseItemListCreateAPIView.as_view(), name='purchase-item-list-create'),
    path('purchase-items/<int:pk>/', PurchaseItemRetrieveUpdateDestroyAPIView.as_view(), name='purchase-item-detail'),
]