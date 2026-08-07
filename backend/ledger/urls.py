from django.urls import path
from ledger.views import LedgerListCreateAPIView, LedgerRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('', LedgerListCreateAPIView.as_view(), name='ledger-list-create'),
    path('<int:pk>/', LedgerRetrieveUpdateDestroyAPIView.as_view(), name='ledger-detail'),
]
