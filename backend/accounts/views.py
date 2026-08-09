from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.serializers import LoginSerializer, JWTLoginSerializer, UserSerializer


class LoginAPIView(APIView):
    """Legacy, message-only login endpoint (unchanged response shape from
    Phase 2). Given the same brute-force scope as the JWT login endpoint
    below (throttle_scope='login') so an attacker can't dodge the rate
    limit by alternating between the two - they share one counter.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response({
            "message": "Login successful",
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class JWTLoginAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        serializer = JWTLoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }, status=status.HTTP_200_OK)


class PublicTokenRefreshView(TokenRefreshView):
    """simplejwt's TokenRefreshView with no permission_classes override of
    its own - it would otherwise inherit the project's global
    IsAuthenticated default, which breaks the entire point of a refresh
    token (using it specifically once the access token has expired).
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'refresh'


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            raise ValidationError({'refresh': 'Refresh token is required.'})

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            raise ValidationError({'refresh': 'Invalid or already blacklisted refresh token.'})

        return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)


class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
