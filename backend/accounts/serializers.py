from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """Used for login/me responses. Deliberately exposes a computed `role`
    label only (Admin/Manager/Staff) - never the raw is_staff, is_superuser,
    or groups fields, so Django Admin access and group membership internals
    are never leaked even though the frontend needs to know the role for
    navigation. Frontend role-based hiding is UX only; every endpoint still
    enforces its own permission_classes regardless of what this reports.
    """
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role']

    def get_role(self, obj):
        if obj.is_superuser:
            return 'Admin'
        names = set(obj.groups.values_list('name', flat=True))
        if 'Manager' in names:
            return 'Manager'
        if 'Staff' in names:
            return 'Staff'
        return None


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
