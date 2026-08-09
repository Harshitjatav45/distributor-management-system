from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs.get('username'),
            password=attrs.get('password'),
        )
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        attrs['user'] = user
        return attrs


class JWTLoginSerializer(serializers.Serializer):
    """Same authenticate() logic as LoginSerializer (including Django's
    built-in inactive-user rejection), but raises AuthenticationFailed
    (HTTP 401) instead of ValidationError (HTTP 400) - kept as a separate
    class so the existing /api/accounts/login/ endpoint's response code is
    never touched by this phase.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs.get('username'),
            password=attrs.get('password'),
        )
        if not user:
            raise AuthenticationFailed("Invalid username or password.")
        attrs['user'] = user
        return attrs
