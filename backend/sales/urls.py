from django.urls import path
from sales.views import (
    SalesListCreateAPIView, SalesRetrieveUpdateDestroyAPIView,
    SalesItemListCreateAPIView, SalesItemRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path('', SalesListCreateAPIView.as_view(), name='sales-list-create'),
    path('<int:pk>/', SalesRetrieveUpdateDestroyAPIView.as_view(), name='sales-detail'),
    path('sales-items/', SalesItemListCreateAPIView.as_view(), name='sales-item-list-create'),
    path('sales-items/<int:pk>/', SalesItemRetrieveUpdateDestroyAPIView.as_view(), name='sales-item-detail'),
]
