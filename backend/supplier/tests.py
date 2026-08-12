from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from dms_test_helpers import make_admin, make_manager, make_staff, auth_headers


class SupplierCRUDTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('sup_admin')
        self.manager = make_manager('sup_manager')
        self.staff = make_staff('sup_staff')

    def _payload(self, **overrides):
        payload = {'supplier_name': 'Rathi Traders', 'supplier_code': 'RATHI01'}
        payload.update(overrides)
        return payload

    def test_create_and_list(self):
        created = self.client.post('/api/supplier/', self._payload(), format='json', **auth_headers(self.staff))
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        listing = self.client.get('/api/supplier/', **auth_headers(self.staff))
        self.assertEqual(listing.status_code, status.HTTP_200_OK)

    def test_duplicate_supplier_code_rejected(self):
        self.client.post('/api/supplier/', self._payload(), format='json', **auth_headers(self.admin))
        dup = self.client.post('/api/supplier/', self._payload(supplier_name='Other'), format='json', **auth_headers(self.admin))
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_opening_balance_rejected(self):
        resp = self.client.post('/api/supplier/', self._payload(opening_balance='-100.00'), format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_credit_limit_rejected(self):
        resp = self.client.post('/api/supplier/', self._payload(credit_limit='-5'), format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_credit_days_rejected(self):
        resp = self.client.post('/api/supplier/', self._payload(credit_days=-1), format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_is_admin_only(self):
        created = self.client.post('/api/supplier/', self._payload(), format='json', **auth_headers(self.admin))
        supplier_id = created.data['id']
        self.assertEqual(self.client.delete(f'/api/supplier/{supplier_id}/', **auth_headers(self.staff)).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(f'/api/supplier/{supplier_id}/', **auth_headers(self.admin)).status_code, status.HTTP_204_NO_CONTENT)
