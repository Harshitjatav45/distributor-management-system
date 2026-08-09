from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import JWTLoginAPIView, LogoutAPIView, CurrentUserAPIView

urlpatterns = [
    path('login/', JWTLoginAPIView.as_view(), name='jwt-login'),
    path('refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),
    path('logout/', LogoutAPIView.as_view(), name='jwt-logout'),
    path('me/', CurrentUserAPIView.as_view(), name='jwt-me'),
]
