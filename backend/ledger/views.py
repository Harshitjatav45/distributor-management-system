from rest_framework import generics
from ledger.models import Ledger
from ledger.serializers import LedgerSerializer


class LedgerListCreateAPIView(generics.ListCreateAPIView):
    queryset = Ledger.objects.all().order_by("-transaction_date", "-id")
    serializer_class = LedgerSerializer


class LedgerRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ledger.objects.all().order_by("-transaction_date", "-id")
    serializer_class = LedgerSerializer
