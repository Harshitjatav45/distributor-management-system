from django.core.cache import cache
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.test import APITestCase
from company.models import Company
from category.models import Category
from material.models import Material
from stock.models import Stock
from dms_test_helpers import make_admin, make_manager, make_staff, auth_headers


class StockPermissionAndValidationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('stk_admin')
        self.manager = make_manager('stk_manager')
        self.staff = make_staff('stk_staff')
        company = Company.objects.create(company_name='Stock Co', company_code='STKCO01')
        category = Category.objects.create(category_name='Stock Cat')
        self.material = Material.objects.create(
            material_name='Stock Material', material_code='STKMAT01',
            company=company, category=category,
            mrp=100, purchase_price=80, selling_price=90, gst_percentage=18,
        )
        self.stock = Stock.objects.create(material=self.material, current_stock=100, available_stock=100)

    def test_all_roles_can_read(self):
        for user in (self.admin, self.manager, self.staff):
            with self.subTest(user=user.username):
                resp = self.client.get('/api/stock/', **auth_headers(user))
                self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_staff_cannot_write(self):
        resp = self.client.patch(f'/api/stock/{self.stock.id}/', {'current_stock': '50'}, format='json', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_write(self):
        resp = self.client.patch(f'/api/stock/{self.stock.id}/', {'current_stock': '150', 'available_stock': '150'}, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_is_admin_only(self):
        self.assertEqual(self.client.delete(f'/api/stock/{self.stock.id}/', **auth_headers(self.manager)).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(f'/api/stock/{self.stock.id}/', **auth_headers(self.admin)).status_code, status.HTTP_204_NO_CONTENT)

    def test_reserved_stock_cannot_exceed_current_stock(self):
        resp = self.client.patch(f'/api/stock/{self.stock.id}/', {'reserved_stock': '200'}, format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_available_stock_cannot_exceed_current_stock(self):
        resp = self.client.patch(f'/api/stock/{self.stock.id}/', {'available_stock': '200'}, format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_current_stock_rejected(self):
        resp = self.client.patch(f'/api/stock/{self.stock.id}/', {'current_stock': '-10'}, format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reserved_exceeding_current_rejected_at_db_level(self):
        """DB-level CheckConstraint mirroring the serializer rule - proves
        it's real enforcement, not just an API-layer check."""
        self.stock.reserved_stock = 200  # current_stock is 100
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.stock.save()
