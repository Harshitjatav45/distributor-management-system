from django.urls import path
from material.views import MaterialListCreateAPIView, MaterialRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('', MaterialListCreateAPIView.as_view(), name='material-list-create'),
    path('<int:pk>/', MaterialRetrieveUpdateDestroyAPIView.as_view(), name='material-detail'),
]
