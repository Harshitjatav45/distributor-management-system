from rest_framework import generics
from company.models import Company
from company.serializers import CompanySerializer
from accounts.permissions import DenyDeleteUnlessAdmin


class CompanyListCreateAPIView(generics.ListCreateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [DenyDeleteUnlessAdmin]


class CompanyRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [DenyDeleteUnlessAdmin]
