from rest_framework import generics
from company.models import Company
from company.serializers import CompanySerializer
from accounts.permissions import DenyDeleteUnlessAdmin
from audit.mixins import AuditedMasterDataMixin


class CompanyListCreateAPIView(AuditedMasterDataMixin, generics.ListCreateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [DenyDeleteUnlessAdmin]
    audit_repr_field = 'company_name'


class CompanyRetrieveUpdateDestroyAPIView(AuditedMasterDataMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [DenyDeleteUnlessAdmin]
    audit_repr_field = 'company_name'
