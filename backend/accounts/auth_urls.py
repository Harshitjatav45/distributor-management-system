from django.urls import path
from accounts.views import JWTLoginAPIView, PublicTokenRefreshView, LogoutAPIView, CurrentUserAPIView

urlpatterns = [
    path('login/', JWTLoginAPIView.as_view(), name='jwt-login'),
    path('refresh/', PublicTokenRefreshView.as_view(), name='jwt-refresh'),
    path('logout/', LogoutAPIView.as_view(), name='jwt-logout'),
    path('me/', CurrentUserAPIView.as_view(), name='jwt-me'),
]
