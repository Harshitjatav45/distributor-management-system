from rest_framework import generics
from material.models import Material
from material.serializers import MaterialSerializer
from accounts.permissions import DenyDeleteUnlessAdmin
from audit.mixins import AuditedMasterDataMixin


class MaterialListCreateAPIView(AuditedMasterDataMixin, generics.ListCreateAPIView):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [DenyDeleteUnlessAdmin]
    audit_repr_field = 'material_name'


class MaterialRetrieveUpdateDestroyAPIView(AuditedMasterDataMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [DenyDeleteUnlessAdmin]
    audit_repr_field = 'material_name'
