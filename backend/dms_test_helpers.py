"""Shared test fixtures for the committed backend test suite.

Deliberately named to NOT match Django's default test-discovery pattern
(`test*.py`) so it is only ever imported, never collected as a test module
itself. Every helper here only ever touches whatever database Django's
test runner has activated for the current run (the isolated `test_*`
database) - these helpers are never used outside `manage.py test`.
"""
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User

ADMIN_PASSWORD = 'AdminTestPass!234'
MANAGER_PASSWORD = 'ManagerTestPass!234'
STAFF_PASSWORD = 'StaffTestPass!234'


def make_admin(username='test_admin'):
    return User.objects.create_superuser(username, f'{username}@example.com', ADMIN_PASSWORD)


def make_manager(username='test_manager'):
    user = User.objects.create_user(username, password=MANAGER_PASSWORD)
    group, _ = Group.objects.get_or_create(name='Manager')
    user.groups.add(group)
    return user


def make_staff(username='test_staff'):
    user = User.objects.create_user(username, password=STAFF_PASSWORD)
    group, _ = Group.objects.get_or_create(name='Staff')
    user.groups.add(group)
    return user


def make_norole(username='test_norole'):
    return User.objects.create_user(username, password='NoRolePass!234')


def auth_headers(user):
    """Bearer-auth kwargs for APIClient.get/post/etc: **auth_headers(user)"""
    token = RefreshToken.for_user(user)
    return {'HTTP_AUTHORIZATION': f'Bearer {token.access_token}'}
