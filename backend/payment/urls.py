from django.urls import path
from payment.views import PaymentListCreateAPIView, PaymentRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('', PaymentListCreateAPIView.as_view(), name='payment-list-create'),
    path('<int:pk>/', PaymentRetrieveUpdateDestroyAPIView.as_view(), name='payment-detail'),
]
