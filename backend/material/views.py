from rest_framework import generics
from material.models import Material
from material.serializers import MaterialSerializer
from accounts.permissions import DenyDeleteUnlessAdmin


class MaterialListCreateAPIView(generics.ListCreateAPIView):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [DenyDeleteUnlessAdmin]


class MaterialRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [DenyDeleteUnlessAdmin]
