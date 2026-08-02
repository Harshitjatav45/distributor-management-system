from django.urls import path
from category.views import CategoryListCreateAPIView, CategoryRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('<int:pk>/', CategoryRetrieveUpdateDestroyAPIView.as_view(), name='category-detail'),
]
