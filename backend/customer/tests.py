from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from dms_test_helpers import make_admin, make_manager, make_staff, auth_headers


class CustomerCRUDTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('cus_admin')
        self.manager = make_manager('cus_manager')
        self.staff = make_staff('cus_staff')

    def _payload(self, **overrides):
        payload = {'customer_name': 'Sharma Traders', 'customer_code': 'SHARMA01'}
        payload.update(overrides)
        return payload

    def test_create_and_list(self):
        created = self.client.post('/api/customer/', self._payload(), format='json', **auth_headers(self.staff))
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        listing = self.client.get('/api/customer/', **auth_headers(self.staff))
        self.assertEqual(listing.status_code, status.HTTP_200_OK)

    def test_duplicate_customer_code_rejected(self):
        self.client.post('/api/customer/', self._payload(), format='json', **auth_headers(self.admin))
        dup = self.client.post('/api/customer/', self._payload(customer_name='Other'), format='json', **auth_headers(self.admin))
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_opening_balance_rejected(self):
        resp = self.client.post('/api/customer/', self._payload(opening_balance='-1'), format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_is_admin_only(self):
        created = self.client.post('/api/customer/', self._payload(), format='json', **auth_headers(self.admin))
        customer_id = created.data['id']
        self.assertEqual(self.client.delete(f'/api/customer/{customer_id}/', **auth_headers(self.manager)).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(f'/api/customer/{customer_id}/', **auth_headers(self.admin)).status_code, status.HTTP_204_NO_CONTENT)
