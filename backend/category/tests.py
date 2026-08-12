from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from dms_test_helpers import make_admin, make_manager, make_staff, auth_headers


class CategoryCRUDTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('cat_admin')
        self.manager = make_manager('cat_manager')
        self.staff = make_staff('cat_staff')

    def test_create_list_update(self):
        created = self.client.post('/api/category/', {'category_name': 'Pipes'}, format='json', **auth_headers(self.staff))
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        listing = self.client.get('/api/category/', **auth_headers(self.staff))
        self.assertEqual(listing.status_code, status.HTTP_200_OK)

        updated = self.client.patch(f'/api/category/{created.data["id"]}/', {'description': 'Steel pipes'}, format='json', **auth_headers(self.manager))
        self.assertEqual(updated.status_code, status.HTTP_200_OK)

    def test_blank_name_rejected(self):
        resp = self.client.post('/api/category/', {'category_name': '  '}, format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_category_code_rejected(self):
        self.client.post('/api/category/', {'category_name': 'A', 'category_code': 'CODE1'}, format='json', **auth_headers(self.admin))
        dup = self.client.post('/api/category/', {'category_name': 'B', 'category_code': 'CODE1'}, format='json', **auth_headers(self.admin))
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_blank_category_code_allowed(self):
        """category_code is nullable/blank - unlike company_code/material_code
        it must NOT be treated as required."""
        resp = self.client.post('/api/category/', {'category_name': 'No Code Category'}, format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_delete_is_admin_only(self):
        created = self.client.post('/api/category/', {'category_name': 'Deletable'}, format='json', **auth_headers(self.admin))
        cat_id = created.data['id']
        self.assertEqual(self.client.delete(f'/api/category/{cat_id}/', **auth_headers(self.staff)).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(f'/api/category/{cat_id}/', **auth_headers(self.admin)).status_code, status.HTTP_204_NO_CONTENT)
