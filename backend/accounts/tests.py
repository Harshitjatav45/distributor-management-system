from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from accounts.models import User
from dms_test_helpers import (
    make_admin, make_manager, make_staff, auth_headers,
    ADMIN_PASSWORD, MANAGER_PASSWORD, STAFF_PASSWORD,
)


class AuthenticationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.active_user = make_staff('auth_active')
        self.inactive_user = make_staff('auth_inactive')
        self.inactive_user.is_active = False
        self.inactive_user.save()

    def test_valid_login_returns_tokens_and_safe_user(self):
        resp = self.client.post('/api/auth/login/', {'username': 'auth_active', 'password': STAFF_PASSWORD}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)
        self.assertEqual(resp.data['user']['username'], 'auth_active')
        self.assertNotIn('password', resp.data['user'])
        self.assertNotIn('groups', resp.data['user'])
        self.assertNotIn('is_superuser', resp.data['user'])

    def test_invalid_username_rejected(self):
        resp = self.client.post('/api/auth/login/', {'username': 'nobody', 'password': 'whatever'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_password_rejected(self):
        resp = self.client.post('/api/auth/login/', {'username': 'auth_active', 'password': 'wrongpass'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_user_cannot_login(self):
        resp = self.client.post('/api/auth/login/', {'username': 'auth_inactive', 'password': STAFF_PASSWORD}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_requires_token(self):
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_rejected(self):
        resp = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION='Bearer not.a.valid.token')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_token_reaches_protected_endpoint(self):
        resp = self.client.get('/api/auth/me/', **auth_headers(self.active_user))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['username'], 'auth_active')

    def test_refresh_issues_new_access_and_rotates_refresh(self):
        login = self.client.post('/api/auth/login/', {'username': 'auth_active', 'password': STAFF_PASSWORD}, format='json')
        old_access = login.data['access']
        old_refresh = login.data['refresh']

        resp = self.client.post('/api/auth/refresh/', {'refresh': old_refresh}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)
        self.assertNotEqual(resp.data['access'], old_access)
        self.assertNotEqual(resp.data['refresh'], old_refresh)

    def test_rotated_refresh_token_is_blacklisted(self):
        login = self.client.post('/api/auth/login/', {'username': 'auth_active', 'password': STAFF_PASSWORD}, format='json')
        old_refresh = login.data['refresh']

        self.client.post('/api/auth/refresh/', {'refresh': old_refresh}, format='json')

        reuse = self.client.post('/api/auth/refresh/', {'refresh': old_refresh}, format='json')
        self.assertEqual(reuse.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_refresh_token(self):
        login = self.client.post('/api/auth/login/', {'username': 'auth_active', 'password': STAFF_PASSWORD}, format='json')
        access = login.data['access']
        refresh = login.data['refresh']

        logout = self.client.post('/api/auth/logout/', {'refresh': refresh}, format='json', HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(logout.status_code, status.HTTP_200_OK)

        reuse = self.client.post('/api/auth/refresh/', {'refresh': refresh}, format='json')
        self.assertEqual(reuse.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_user_with_previously_issued_token_is_rejected(self):
        """simplejwt re-checks is_active on every authenticated request, not
        just at login - deactivating a user must invalidate their existing,
        unexpired access token immediately."""
        token = RefreshToken.for_user(self.active_user)
        access = str(token.access_token)

        still_active = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(still_active.status_code, status.HTTP_200_OK)

        self.active_user.is_active = False
        self.active_user.save()

        now_rejected = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(now_rejected.status_code, status.HTTP_401_UNAUTHORIZED)


class RBACCrossCuttingTests(APITestCase):
    """Endpoint-level RBAC checks that don't belong to any single business
    module - direct API access regardless of what the frontend would show.
    """
    def setUp(self):
        cache.clear()
        self.admin = make_admin('rbac_admin')
        self.manager = make_manager('rbac_manager')
        self.staff = make_staff('rbac_staff')

    def test_unauthenticated_request_rejected_everywhere(self):
        for path in ['/api/company/', '/api/purchase/', '/api/payment/', '/api/ledger/', '/api/users/', '/api/audit/']:
            with self.subTest(path=path):
                resp = self.client.get(path)
                self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_cannot_reach_payment_ledger_users_audit(self):
        for path in ['/api/payment/', '/api/ledger/', '/api/users/', '/api/audit/']:
            with self.subTest(path=path):
                resp = self.client.get(path, **auth_headers(self.staff))
                self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_cannot_reach_users_or_audit(self):
        for path in ['/api/users/', '/api/audit/']:
            with self.subTest(path=path):
                resp = self.client.get(path, **auth_headers(self.manager))
                self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_reach_payment_and_ledger(self):
        for path in ['/api/payment/', '/api/ledger/']:
            with self.subTest(path=path):
                resp = self.client.get(path, **auth_headers(self.manager))
                self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_admin_can_reach_everything(self):
        for path in ['/api/company/', '/api/payment/', '/api/ledger/', '/api/users/', '/api/audit/']:
            with self.subTest(path=path):
                resp = self.client.get(path, **auth_headers(self.admin))
                self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_master_data_delete_is_admin_only(self):
        from company.models import Company
        company = Company.objects.create(company_name='RBAC Test Co', company_code='RBACTC01')

        staff_delete = self.client.delete(f'/api/company/{company.id}/', **auth_headers(self.staff))
        self.assertEqual(staff_delete.status_code, status.HTTP_403_FORBIDDEN)

        manager_delete = self.client.delete(f'/api/company/{company.id}/', **auth_headers(self.manager))
        self.assertEqual(manager_delete.status_code, status.HTTP_403_FORBIDDEN)

        admin_delete = self.client.delete(f'/api/company/{company.id}/', **auth_headers(self.admin))
        self.assertEqual(admin_delete.status_code, status.HTTP_204_NO_CONTENT)


class UserManagementTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('um_admin')
        self.manager = make_manager('um_manager')
        self.staff = make_staff('um_staff')

    def test_admin_can_create_staff_user(self):
        resp = self.client.post('/api/users/', {
            'username': 'new_staff_1', 'password': 'BrandNewPass!234', 'group': 'Staff',
        }, format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['role'], 'Staff')
        self.assertNotIn('password', resp.data)

    def test_manager_and_staff_fully_blocked_from_user_management(self):
        for user in (self.manager, self.staff):
            with self.subTest(user=user.username):
                resp = self.client.get('/api/users/', **auth_headers(user))
                self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
                create = self.client.post('/api/users/', {'username': 'x', 'password': 'x', 'group': 'Staff'}, format='json', **auth_headers(user))
                self.assertEqual(create.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_assign_admin_group_via_api(self):
        resp = self.client.post('/api/users/', {
            'username': 'should_fail', 'password': 'SomePass!234', 'group': 'Admin',
        }, format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_rejected(self):
        resp = self.client.post('/api/users/', {
            'username': 'weak_pw_user', 'password': '123', 'group': 'Staff',
        }, format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activate_deactivate_and_role_change(self):
        target = make_staff('um_target')
        resp = self.client.patch(f'/api/users/{target.id}/', {'is_active': False}, format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['is_active'])

        resp = self.client.patch(f'/api/users/{target.id}/', {'group': 'Manager'}, format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['role'], 'Manager')

    def test_admin_can_set_target_password(self):
        target = make_staff('um_pw_target')
        resp = self.client.post(f'/api/users/{target.id}/set-password/', {'new_password': 'AnotherPass!234'}, format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', str(resp.data).lower().replace('password updated', ''))
        target.refresh_from_db()
        self.assertTrue(target.check_password('AnotherPass!234'))

    def test_superuser_excluded_from_user_management_api(self):
        resp = self.client.get('/api/users/', **auth_headers(self.admin))
        usernames = [u['username'] for u in resp.data['results']]
        self.assertNotIn('um_admin', usernames)

        detail = self.client.get(f'/api/users/{self.admin.id}/', **auth_headers(self.admin))
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_me_endpoint_never_exposes_writable_role_fields(self):
        resp = self.client.get('/api/auth/me/', **auth_headers(self.staff))
        for forbidden in ('groups', 'is_staff', 'is_superuser', 'password'):
            self.assertNotIn(forbidden, resp.data)
