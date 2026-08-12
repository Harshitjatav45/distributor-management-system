from django.core.cache import cache
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.test import APITestCase
from company.models import Company
from category.models import Category
from material.models import Material
from dms_test_helpers import make_admin, make_manager, make_staff, auth_headers


class MaterialCRUDTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('mat_admin')
        self.manager = make_manager('mat_manager')
        self.staff = make_staff('mat_staff')
        self.company = Company.objects.create(company_name='Mat Co', company_code='MATCO01')
        self.category = Category.objects.create(category_name='Mat Cat')

    def _payload(self, **overrides):
        payload = {
            'material_name': 'Steel Rod', 'material_code': 'ROD001',
            'company': self.company.id, 'category': self.category.id,
            'mrp': '150.00', 'purchase_price': '100.00', 'selling_price': '120.00', 'gst_percentage': '18.00',
        }
        payload.update(overrides)
        return payload

    def test_create_requires_company_and_category(self):
        resp = self.client.post('/api/material/', self._payload(), format='json', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_selling_price_below_purchase_price_rejected(self):
        resp = self.client.post('/api/material/', self._payload(selling_price='50.00'), format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mrp_below_selling_price_rejected(self):
        resp = self.client.post('/api/material/', self._payload(mrp='50.00'), format='json', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_material_code_rejected(self):
        self.client.post('/api/material/', self._payload(), format='json', **auth_headers(self.admin))
        dup = self.client.post('/api/material/', self._payload(material_name='Different'), format='json', **auth_headers(self.admin))
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_barcode_rejected(self):
        self.client.post('/api/material/', self._payload(material_code='ROD002', barcode='BC001'), format='json', **auth_headers(self.admin))
        dup = self.client.post('/api/material/', self._payload(material_code='ROD003', barcode='BC001'), format='json', **auth_headers(self.admin))
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_blank_barcode_does_not_collide(self):
        """barcode is unique=True but blank/null - two materials with no
        barcode must not be treated as duplicates of each other."""
        first = self.client.post('/api/material/', self._payload(material_code='ROD004'), format='json', **auth_headers(self.admin))
        second = self.client.post('/api/material/', self._payload(material_code='ROD005'), format='json', **auth_headers(self.admin))
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)

    def test_delete_is_admin_only(self):
        created = self.client.post('/api/material/', self._payload(), format='json', **auth_headers(self.admin))
        mat_id = created.data['id']
        self.assertEqual(self.client.delete(f'/api/material/{mat_id}/', **auth_headers(self.manager)).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(f'/api/material/{mat_id}/', **auth_headers(self.admin)).status_code, status.HTTP_204_NO_CONTENT)


class MaterialDatabaseConstraintTests(APITestCase):
    """Proves the DB-level CheckConstraints added in Phase 4 are real
    enforcement, not just serializer-level validation - a direct ORM
    .save() bypassing the serializer entirely must still be rejected by
    PostgreSQL itself."""

    def setUp(self):
        self.company = Company.objects.create(company_name='Constraint Co', company_code='CONSTR01')
        self.category = Category.objects.create(category_name='Constraint Cat')

    def test_negative_purchase_price_rejected_at_db_level(self):
        material = Material(
            material_name='Bad Material', material_code='BADMAT01',
            company=self.company, category=self.category,
            mrp=100, purchase_price=-1, selling_price=50, gst_percentage=18,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                material.save()

    def test_negative_gst_percentage_rejected_at_db_level(self):
        material = Material(
            material_name='Bad Material 2', material_code='BADMAT02',
            company=self.company, category=self.category,
            mrp=100, purchase_price=50, selling_price=80, gst_percentage=-5,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                material.save()
