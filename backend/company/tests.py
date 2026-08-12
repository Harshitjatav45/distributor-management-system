from django.core.cache import cache
from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.test import APITestCase
from company.models import Company
from dms_test_helpers import make_admin, make_manager, make_staff, auth_headers


class CompanyCRUDTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('co_admin')
        self.manager = make_manager('co_manager')
        self.staff = make_staff('co_staff')

    def _payload(self, **overrides):
        payload = {'company_name': 'Test Co', 'company_code': 'TESTCO01'}
        payload.update(overrides)
        return payload

    def test_staff_can_create_and_list(self):
        resp = self.client.post('/api/company/', self._payload(), format='json', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        listing = self.client.get('/api/company/', **auth_headers(self.staff))
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertIn('results', listing.data)
        self.assertIn('count', listing.data)

    def test_blank_name_rejected(self):
        resp = self.client.post('/api/company/', self._payload(company_name='   '), format='json', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_company_code_rejected(self):
        self.client.post('/api/company/', self._payload(), format='json', **auth_headers(self.admin))
        dup = self.client.post('/api/company/', self._payload(company_name='Different Name'), format='json', **auth_headers(self.admin))
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_and_manager_can_update(self):
        created = self.client.post('/api/company/', self._payload(), format='json', **auth_headers(self.admin))
        company_id = created.data['id']

        staff_update = self.client.patch(f'/api/company/{company_id}/', {'city': 'Jaipur'}, format='json', **auth_headers(self.staff))
        self.assertEqual(staff_update.status_code, status.HTTP_200_OK)

        manager_update = self.client.patch(f'/api/company/{company_id}/', {'city': 'Udaipur'}, format='json', **auth_headers(self.manager))
        self.assertEqual(manager_update.status_code, status.HTTP_200_OK)

    def test_delete_is_admin_only(self):
        created = self.client.post('/api/company/', self._payload(), format='json', **auth_headers(self.admin))
        company_id = created.data['id']

        self.assertEqual(
            self.client.delete(f'/api/company/{company_id}/', **auth_headers(self.staff)).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(f'/api/company/{company_id}/', **auth_headers(self.manager)).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(f'/api/company/{company_id}/', **auth_headers(self.admin)).status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_delete_blocked_when_material_references_company(self):
        from category.models import Category
        from material.models import Material

        company = Company.objects.create(company_name='Protected Co', company_code='PROTCO01')
        category = Category.objects.create(category_name='Protected Cat')
        Material.objects.create(
            material_name='Protected Material', material_code='PROTMAT01',
            company=company, category=category,
            mrp=100, purchase_price=80, selling_price=90, gst_percentage=18,
        )

        # PROTECT FK raises ProtectedError with no custom exception handling
        # (it isn't a DRF APIException, so it propagates rather than
        # becoming a clean 400/403 response) - the important behavioral
        # guarantee under test is that the row is NOT deleted.
        with self.assertRaises(ProtectedError):
            self.client.delete(f'/api/company/{company.id}/', **auth_headers(self.admin))
        self.assertTrue(Company.objects.filter(id=company.id).exists())


class CompanyPaginationAndSearchTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('copag_admin')
        for i in range(30):
            Company.objects.create(company_name=f'Pagination Co {i:02d}', company_code=f'PAGCO{i:02d}')
        Company.objects.create(company_name='Findable Steel Traders', company_code='FINDME01')

    def test_default_page_size_and_envelope_shape(self):
        resp = self.client.get('/api/company/', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(set(resp.data.keys()), {'count', 'next', 'previous', 'results'})
        self.assertEqual(resp.data['count'], 31)
        self.assertEqual(len(resp.data['results']), 25)
        self.assertIsNotNone(resp.data['next'])
        self.assertIsNone(resp.data['previous'])

    def test_second_page_via_next_link(self):
        first = self.client.get('/api/company/', **auth_headers(self.admin))
        second = self.client.get('/api/company/?page=2', **auth_headers(self.admin))
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(len(second.data['results']), 6)
        self.assertIsNone(second.data['next'])
        self.assertIsNotNone(second.data['previous'])
        # No row appears on both pages.
        first_ids = {row['id'] for row in first.data['results']}
        second_ids = {row['id'] for row in second.data['results']}
        self.assertEqual(first_ids & second_ids, set())

    def test_page_size_query_param_respected(self):
        resp = self.client.get('/api/company/?page_size=5', **auth_headers(self.admin))
        self.assertEqual(len(resp.data['results']), 5)

    def test_search_finds_matching_row_regardless_of_page(self):
        resp = self.client.get('/api/company/?search=Findable', **auth_headers(self.admin))
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['company_code'], 'FINDME01')
