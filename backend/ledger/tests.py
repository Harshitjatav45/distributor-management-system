from decimal import Decimal

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from customer.models import Customer
from ledger.models import Ledger
from dms_test_helpers import make_admin, make_manager, make_staff, auth_headers


class LedgerReadOnlyTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('led_admin')
        self.manager = make_manager('led_manager')
        self.staff = make_staff('led_staff')
        self.customer = Customer.objects.create(customer_name='Led Customer', customer_code='LEDCUS01')
        self.entry = Ledger.objects.create(
            transaction_date='2026-01-01', reference_type='OPENING', customer=self.customer,
            entry_type='DEBIT', amount=Decimal('500'), balance=Decimal('500'),
        )

    def test_admin_and_manager_can_read(self):
        for user in (self.admin, self.manager):
            with self.subTest(user=user.username):
                resp = self.client.get('/api/ledger/', **auth_headers(user))
                self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_staff_cannot_read(self):
        resp = self.client.get('/api/ledger/', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_write_methods_all_rejected(self):
        # These are 405s by construction (ListAPIView/RetrieveAPIView have
        # no create/update/destroy mixins at all) - not permission denials.
        self.assertEqual(self.client.post('/api/ledger/', {}, format='json', **auth_headers(self.admin)).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.put(f'/api/ledger/{self.entry.id}/', {}, format='json', **auth_headers(self.admin)).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.patch(f'/api/ledger/{self.entry.id}/', {}, format='json', **auth_headers(self.admin)).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(f'/api/ledger/{self.entry.id}/', **auth_headers(self.admin)).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_staff_write_attempt_rejected_by_permission_before_method_check(self):
        """DRF checks permissions before method-existence, so a Staff user
        (who fails IsAdminOrManager) gets 403 here, not 405 - 405 only
        applies to callers who pass the permission gate (see
        test_write_methods_all_rejected for the admin/405 case)."""
        resp = self.client.post('/api/ledger/', {}, format='json', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_running_balance_persisted_correctly(self):
        second = Ledger.objects.create(
            transaction_date='2026-01-02', reference_type='SALES', customer=self.customer,
            entry_type='DEBIT', amount=Decimal('200'), balance=Decimal('700'),
        )
        resp = self.client.get(f'/api/ledger/{second.id}/', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(resp.data['balance']), Decimal('700.00'))
