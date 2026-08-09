"""
Role-based access control for this project.

Deliberately NOT built on Django's per-model Permission objects (add_x/
change_x/view_x). The access rules for this project are a fixed, fully
specified matrix (Admin/Manager/Staff x module), not something meant to be
freely reconfigured via checkboxes in Django Admin - so the actual rule
lives here, in readable Python, keyed off Group *membership by name*.
`setup_roles` (accounts/management/commands/setup_roles.py) is responsible
only for making sure the 'Manager' and 'Staff' groups exist; it does not
assign any Django Permission objects to them, because nothing in this file
consults request.user.has_perm().

Role mapping:
- Admin   = request.user.is_superuser (Django-native, bypasses everything -
  no 'Admin' Group is created; see the approved design for why).
- Manager = member of the 'Manager' Group.
- Staff   = member of the 'Staff' Group (NOT the same thing as Django's own
  is_staff flag, which is reserved for Django Admin access only).
"""
from rest_framework.permissions import BasePermission


def is_admin(user):
    return bool(user and user.is_authenticated and user.is_superuser)


def is_in_group(user, group_name):
    return bool(user and user.is_authenticated and user.groups.filter(name=group_name).exists())


def is_manager(user):
    return is_in_group(user, 'Manager')


def is_staff_role(user):
    return is_in_group(user, 'Staff')


def is_admin_or_manager(user):
    return is_admin(user) or is_manager(user)


class IsAdminOrManager(BasePermission):
    """Admin (superuser) or a member of the Manager group. Used for Ledger
    read, Payment (all access), financial reports, and Stock writes.
    """
    def has_permission(self, request, view):
        return is_admin_or_manager(request.user)


class DenyDeleteUnlessAdmin(BasePermission):
    """Any authenticated user (Admin/Manager/Staff) for read/write; DELETE
    reserved for Admin only. Used for master-data modules and the
    Purchase/Sales header records.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method == 'DELETE':
            return is_admin(request.user)
        return True


class StockPermission(BasePermission):
    """Read for any authenticated role; create/update for Admin/Manager
    only; delete for Admin only. Staff is read-only on Stock.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if request.method == 'DELETE':
            return is_admin(request.user)
        return is_admin_or_manager(request.user)
