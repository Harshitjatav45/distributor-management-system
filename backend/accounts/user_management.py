import logging
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import User
from accounts.permissions import IsAdminOnly
from audit.services import write_audit

logger = logging.getLogger(__name__)

# The approved RBAC design has no 'Admin' Group - Admin is is_superuser=True,
# managed outside this API (Django Admin / manage.py createsuperuser). This
# endpoint can only ever place a user into Manager or Staff, and every
# queryset below excludes superusers - so there is no code path here that
# can create, promote to, or otherwise touch an Admin account. That
# structurally prevents Staff->Manager/Admin, Manager->Admin, and
# Manager->superuser escalation: those roles simply aren't reachable
# through this API no matter what a caller submits.
MANAGEABLE_GROUPS = ('Manager', 'Staff')


def _user_role(user):
    if user.is_superuser:
        return 'Admin'
    names = set(user.groups.values_list('name', flat=True))
    if 'Manager' in names:
        return 'Manager'
    if 'Staff' in names:
        return 'Staff'
    return None


def _safe_user_snapshot(user):
    """Fields safe to store in an AuditLog before/after snapshot - never
    password, password hash, or any token.
    """
    return {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active,
        'role': _user_role(user),
    }


class UserManagementSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'role', 'date_joined', 'last_login']
        read_only_fields = fields

    def get_role(self, obj):
        return _user_role(obj)


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True, default='')
    last_name = serializers.CharField(required=False, allow_blank=True, default='')
    email = serializers.EmailField(required=False, allow_blank=True, default='')
    group = serializers.ChoiceField(choices=MANAGEABLE_GROUPS)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def create(self, validated_data):
        group_name = validated_data.pop('group')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        # Never settable from this API: is_staff (Django Admin access) and
        # is_superuser (Admin role) both stay False for every user created
        # here, by construction.
        user.is_staff = False
        user.is_superuser = False
        user.save()
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.set([group])
        return user


class UserRoleUpdateSerializer(serializers.Serializer):
    group = serializers.ChoiceField(choices=MANAGEABLE_GROUPS, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError('Provide at least one of: group, is_active.')
        return attrs


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value


class UserListCreateAPIView(generics.ListCreateAPIView):
    """Admin-only. Lists/creates Manager and Staff accounts. Superusers are
    excluded from the queryset entirely, so Admin accounts are never
    visible, editable, or reachable through this endpoint.
    """
    permission_classes = [IsAdminOnly]
    queryset = User.objects.filter(is_superuser=False).order_by('username')

    def get_serializer_class(self):
        return UserCreateSerializer if self.request.method == 'POST' else UserManagementSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = serializer.save()
            write_audit(
                actor=request.user,
                action='CREATE',
                model_name='User',
                object_id=user.id,
                object_repr=user.username,
                after=_safe_user_snapshot(user),
            )
        logger.info("User created: username=%s role=%s by=%s", user.username, _user_role(user), request.user.username)
        return Response(UserManagementSerializer(user).data, status=status.HTTP_201_CREATED)


class UserRetrieveUpdateAPIView(generics.RetrieveAPIView):
    """Admin-only. GET returns safe user info; PATCH updates group
    membership and/or is_active. Never accepts password, is_staff, or
    is_superuser - role changes are restricted to Manager/Staff only.
    """
    permission_classes = [IsAdminOnly]
    queryset = User.objects.filter(is_superuser=False)
    serializer_class = UserManagementSerializer

    def patch(self, request, *args, **kwargs):
        target = self.get_object()
        serializer = UserRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            before = _safe_user_snapshot(target)

            if 'group' in data:
                group, _ = Group.objects.get_or_create(name=data['group'])
                target.groups.set([group])
                write_audit(
                    actor=request.user, action='ROLE_CHANGE', model_name='User',
                    object_id=target.id, object_repr=target.username,
                    before=before, after=_safe_user_snapshot(target),
                )

            if 'is_active' in data:
                target.is_active = data['is_active']
                target.save(update_fields=['is_active'])
                write_audit(
                    actor=request.user,
                    action='ACTIVATE' if data['is_active'] else 'DEACTIVATE',
                    model_name='User', object_id=target.id, object_repr=target.username,
                    before=before, after=_safe_user_snapshot(target),
                )

        logger.info("User updated: username=%s by=%s changes=%s", target.username, request.user.username, list(data.keys()))
        return Response(UserManagementSerializer(target).data, status=status.HTTP_200_OK)


class UserSetPasswordAPIView(APIView):
    """Admin-only. Directly sets a Manager/Staff user's password (e.g. after
    a forgotten password) - not a self-service reset flow (no email/token),
    which remains out of scope. Never logs or returns the password value.
    """
    permission_classes = [IsAdminOnly]

    def post(self, request, pk):
        target = get_object_or_404(User.objects.filter(is_superuser=False), pk=pk)
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            target.set_password(serializer.validated_data['new_password'])
            target.save(update_fields=['password'])
            write_audit(
                actor=request.user, action='PASSWORD_CHANGE', model_name='User',
                object_id=target.id, object_repr=target.username,
                metadata={'changed_by_admin': True},
            )

        logger.info("Password changed by admin: username=%s by=%s", target.username, request.user.username)
        return Response({'message': 'Password updated successfully.'}, status=status.HTTP_200_OK)
