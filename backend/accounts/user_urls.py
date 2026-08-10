from django.urls import path
from accounts.user_management import UserListCreateAPIView, UserRetrieveUpdateAPIView, UserSetPasswordAPIView

urlpatterns = [
    path('', UserListCreateAPIView.as_view(), name='user-list-create'),
    path('<int:pk>/', UserRetrieveUpdateAPIView.as_view(), name='user-detail'),
    path('<int:pk>/set-password/', UserSetPasswordAPIView.as_view(), name='user-set-password'),
]
