from rest_framework import generics
from category.models import Category
from category.serializers import CategorySerializer
from accounts.permissions import DenyDeleteUnlessAdmin
from audit.mixins import AuditedMasterDataMixin


class CategoryListCreateAPIView(AuditedMasterDataMixin, generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('category_name')
    serializer_class = CategorySerializer
    permission_classes = [DenyDeleteUnlessAdmin]
    audit_repr_field = 'category_name'
    search_fields = ['category_name', 'category_code']


class CategoryRetrieveUpdateDestroyAPIView(AuditedMasterDataMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [DenyDeleteUnlessAdmin]
    audit_repr_field = 'category_name'
