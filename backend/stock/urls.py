from django.urls import path
from stock.views import StockListCreateAPIView, StockRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('', StockListCreateAPIView.as_view(), name='stock-list-create'),
    path('<int:pk>/', StockRetrieveUpdateDestroyAPIView.as_view(), name='stock-detail'),
]
