from django.urls import path
from ledger.views import LedgerListAPIView, LedgerRetrieveAPIView

urlpatterns = [
    path('', LedgerListAPIView.as_view(), name='ledger-list'),
    path('<int:pk>/', LedgerRetrieveAPIView.as_view(), name='ledger-detail'),
]
