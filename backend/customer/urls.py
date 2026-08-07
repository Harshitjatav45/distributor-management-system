from django.urls import path
from customer.views import CustomerListCreateAPIView, CustomerRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('', CustomerListCreateAPIView.as_view(), name='customer-list-create'),
    path('<int:pk>/', CustomerRetrieveUpdateDestroyAPIView.as_view(), name='customer-detail'),
]
