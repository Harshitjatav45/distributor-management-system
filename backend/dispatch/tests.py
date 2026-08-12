from decimal import Decimal

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from company.models import Company
from category.models import Category
from material.models import Material
from customer.models import Customer
from stock.models import Stock
from sales.models import Sales, SalesItem
from dispatch.models import Dispatch
from dms_test_helpers import make_admin, make_staff, auth_headers


class DispatchWorkflowTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('dsp_admin')
        self.staff = make_staff('dsp_staff')
        self.customer = Customer.objects.create(customer_name='Dsp Customer', customer_code='DSPCUS01')
        company = Company.objects.create(company_name='Dsp Co', company_code='DSPCO01')
        category = Category.objects.create(category_name='Dsp Cat')
        self.material = Material.objects.create(
            material_name='Dsp Material', material_code='DSPMAT01', company=company, category=category,
            mrp=100, purchase_price=50, selling_price=80, gst_percentage=18,
        )
        Stock.objects.create(material=self.material, current_stock=100, available_stock=100)

        self.draft_sales = self._make_sales('DSP-SAL-DRAFT', 'DRAFT')
        self.confirmed_sales = self._make_sales('DSP-SAL-CONF', 'CONFIRMED')

    def _make_sales(self, sales_number, status_value):
        sales = Sales.objects.create(
            sales_number=sales_number, customer=self.customer, sales_date='2026-01-01',
            status=status_value, total_amount=100, gst_amount=18, grand_total=118,
        )
        SalesItem.objects.create(
            sales=sales, material=self.material, quantity=Decimal('5'), unit='PCS', rate=Decimal('80'),
            taxable_amount=Decimal('400'), gst_percentage=18, gst_amount=Decimal('72'), line_total=Decimal('472'),
        )
        return sales

    def test_dispatch_requires_confirmed_sales(self):
        resp = self.client.post('/api/dispatch/', {
            'dispatch_number': 'DSP-001', 'sales': self.draft_sales.id, 'dispatch_date': '2026-01-02',
        }, format='json', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_can_create_dispatch_for_confirmed_sales(self):
        """Matches the approved RBAC design: Staff can fully manage Dispatch."""
        resp = self.client.post('/api/dispatch/', {
            'dispatch_number': 'DSP-002', 'sales': self.confirmed_sales.id, 'dispatch_date': '2026-01-02',
        }, format='json', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data['status'], 'DISPATCHED')

    def test_duplicate_active_dispatch_blocked(self):
        self.client.post('/api/dispatch/', {
            'dispatch_number': 'DSP-003', 'sales': self.confirmed_sales.id, 'dispatch_date': '2026-01-02',
        }, format='json', **auth_headers(self.staff))
        dup = self.client.post('/api/dispatch/', {
            'dispatch_number': 'DSP-004', 'sales': self.confirmed_sales.id, 'dispatch_date': '2026-01-02',
        }, format='json', **auth_headers(self.staff))
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_dispatch_allowed_after_previous_one_cancelled(self):
        first = self.client.post('/api/dispatch/', {
            'dispatch_number': 'DSP-005', 'sales': self.confirmed_sales.id, 'dispatch_date': '2026-01-02',
        }, format='json', **auth_headers(self.staff))
        self.client.patch(f'/api/dispatch/{first.data["id"]}/', {'status': 'CANCELLED'}, format='json', **auth_headers(self.staff))

        second = self.client.post('/api/dispatch/', {
            'dispatch_number': 'DSP-006', 'sales': self.confirmed_sales.id, 'dispatch_date': '2026-01-02',
        }, format='json', **auth_headers(self.staff))
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)

    def test_valid_status_transitions(self):
        created = self.client.post('/api/dispatch/', {
            'dispatch_number': 'DSP-007', 'sales': self.confirmed_sales.id, 'dispatch_date': '2026-01-02',
        }, format='json', **auth_headers(self.staff))
        dispatch_id = created.data['id']

        step1 = self.client.patch(f'/api/dispatch/{dispatch_id}/', {'status': 'OUT_FOR_DELIVERY'}, format='json', **auth_headers(self.staff))
        self.assertEqual(step1.status_code, status.HTTP_200_OK)

        step2 = self.client.patch(f'/api/dispatch/{dispatch_id}/', {'status': 'DELIVERED'}, format='json', **auth_headers(self.staff))
        self.assertEqual(step2.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(step2.data['actual_delivery_date'])

    def test_delivered_is_a_terminal_state(self):
        created = self.client.post('/api/dispatch/', {
            'dispatch_number': 'DSP-008', 'sales': self.confirmed_sales.id, 'dispatch_date': '2026-01-02',
        }, format='json', **auth_headers(self.staff))
        dispatch_id = created.data['id']
        self.client.patch(f'/api/dispatch/{dispatch_id}/', {'status': 'DELIVERED'}, format='json', **auth_headers(self.staff))

        resp = self.client.patch(f'/api/dispatch/{dispatch_id}/', {'status': 'CANCELLED'}, format='json', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_hard_delete_is_blocked(self):
        created = self.client.post('/api/dispatch/', {
            'dispatch_number': 'DSP-009', 'sales': self.confirmed_sales.id, 'dispatch_date': '2026-01-02',
        }, format='json', **auth_headers(self.staff))
        resp = self.client.delete(f'/api/dispatch/{created.data["id"]}/', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Dispatch.objects.filter(id=created.data['id']).exists())

    def test_by_sales_endpoint(self):
        self.client.post('/api/dispatch/', {
            'dispatch_number': 'DSP-010', 'sales': self.confirmed_sales.id, 'dispatch_date': '2026-01-02',
        }, format='json', **auth_headers(self.staff))
        resp = self.client.get(f'/api/dispatch/by-sales/{self.confirmed_sales.id}/', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
