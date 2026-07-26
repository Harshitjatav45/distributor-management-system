from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.serializers import LoginSerializer, UserSerializer


class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response({
            "message": "Login successful",
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)
