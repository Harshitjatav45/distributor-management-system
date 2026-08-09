from rest_framework import generics
from category.models import Category
from category.serializers import CategorySerializer
from accounts.permissions import DenyDeleteUnlessAdmin


class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [DenyDeleteUnlessAdmin]


class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [DenyDeleteUnlessAdmin]
