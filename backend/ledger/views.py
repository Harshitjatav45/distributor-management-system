from rest_framework import generics
from ledger.models import Ledger
from ledger.serializers import LedgerSerializer
from accounts.permissions import IsAdminOrManager

# Ledger is an append-only audit trail. Entries are created exclusively by
# the Purchase/Sales/Payment services (via Ledger.objects.create(), which
# never goes through these views at all). The API therefore exposes only
# ListAPIView/RetrieveAPIView - there is no create/update/destroy mixin to
# even attach a permission check to; POST/PUT/PATCH/DELETE simply don't
# exist on these endpoints (405), rather than being permission-denied (403).


class LedgerListAPIView(generics.ListAPIView):
    queryset = Ledger.objects.all().order_by("-transaction_date", "-id")
    serializer_class = LedgerSerializer
    permission_classes = [IsAdminOrManager]


class LedgerRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Ledger.objects.all().order_by("-transaction_date", "-id")
    serializer_class = LedgerSerializer
    permission_classes = [IsAdminOrManager]
