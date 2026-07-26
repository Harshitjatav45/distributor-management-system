from django.urls import path
from company.views import CompanyListCreateAPIView, CompanyRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('', CompanyListCreateAPIView.as_view(), name='company-list-create'),
    path('<int:pk>/', CompanyRetrieveUpdateDestroyAPIView.as_view(), name='company-detail'),
]
