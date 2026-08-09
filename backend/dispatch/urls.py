from django.urls import path
from dispatch.views import (
    DispatchListCreateAPIView,
    DispatchRetrieveUpdateDestroyAPIView,
    DispatchBySalesAPIView,
)

urlpatterns = [
    path('by-sales/<int:sales_id>/', DispatchBySalesAPIView.as_view(), name='dispatch-by-sales'),
    path('', DispatchListCreateAPIView.as_view(), name='dispatch-list-create'),
    path('<int:pk>/', DispatchRetrieveUpdateDestroyAPIView.as_view(), name='dispatch-detail'),
]
