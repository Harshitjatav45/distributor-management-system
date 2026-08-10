from rest_framework import generics
from category.models import Category
from category.serializers import CategorySerializer
from accounts.permissions import DenyDeleteUnlessAdmin
from audit.mixins import AuditedMasterDataMixin


class CategoryListCreateAPIView(AuditedMasterDataMixin, generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [DenyDeleteUnlessAdmin]
    audit_repr_field = 'category_name'


class CategoryRetrieveUpdateDestroyAPIView(AuditedMasterDataMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [DenyDeleteUnlessAdmin]
    audit_repr_field = 'category_name'
