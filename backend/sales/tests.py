import threading
from decimal import Decimal

from django.core.cache import cache
from django.db import connection
from django.test import TransactionTestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from company.models import Company
from category.models import Category
from material.models import Material
from customer.models import Customer
from stock.models import Stock
from ledger.models import Ledger
from sales.models import Sales, SalesItem
from dispatch.models import Dispatch
from dms_test_helpers import make_admin, make_manager, make_staff, auth_headers


def make_material(code='SALMAT01'):
    company = Company.objects.create(company_name=f'SalCo {code}', company_code=f'SALCO-{code}')
    category = Category.objects.create(category_name=f'SalCat {code}')
    return Material.objects.create(
        material_name=f'Material {code}', material_code=code,
        company=company, category=category,
        mrp=100, purchase_price=50, selling_price=80, gst_percentage=18,
    )


class SalesWorkflowTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('sal_admin')
        self.manager = make_manager('sal_manager')
        self.staff = make_staff('sal_staff')
        self.customer = Customer.objects.create(customer_name='Sal Customer', customer_code='SALCUS01')
        self.material = make_material('SALMAT01')
        self.stock = Stock.objects.create(material=self.material, current_stock=100, available_stock=100)

    def _create_draft(self, sales_number='SAL-TEST-001', user=None):
        user = user or self.staff
        resp = self.client.post('/api/sales/', {
            'sales_number': sales_number, 'customer': self.customer.id, 'sales_date': '2026-01-01',
            'status': 'DRAFT', 'total_amount': '0', 'gst_amount': '0', 'grand_total': '0',
        }, format='json', **auth_headers(user))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        return resp.data['id']

    def _add_item(self, sales_id, quantity='10', rate='80', gst_percentage='18', user=None):
        user = user or self.staff
        resp = self.client.post('/api/sales/sales-items/', {
            'sales': sales_id, 'material': self.material.id, 'quantity': quantity,
            'unit': 'PCS', 'rate': rate, 'gst_percentage': gst_percentage,
            'taxable_amount': str(Decimal(quantity) * Decimal(rate)),
            'gst_amount': str(Decimal(quantity) * Decimal(rate) * Decimal(gst_percentage) / 100),
            'line_total': str(Decimal(quantity) * Decimal(rate) * (1 + Decimal(gst_percentage) / 100)),
        }, format='json', **auth_headers(user))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        return resp.data

    def _confirm(self, sales_id, grand_total, user=None):
        user = user or self.manager
        return self.client.patch(f'/api/sales/{sales_id}/', {
            'status': 'CONFIRMED', 'total_amount': '800', 'gst_amount': '144', 'grand_total': str(grand_total),
        }, format='json', **auth_headers(user))

    def test_staff_cannot_confirm(self):
        sales_id = self._create_draft()
        self._add_item(sales_id)
        resp = self._confirm(sales_id, '944', user=self.staff)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_confirm_deducts_stock_and_posts_debit_ledger(self):
        sales_id = self._create_draft()
        self._add_item(sales_id, quantity='10', rate='80')
        resp = self._confirm(sales_id, '944')
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.current_stock, Decimal('90.000'))
        self.assertEqual(self.stock.available_stock, Decimal('90.000'))

        entry = Ledger.objects.get(reference_type='SALES', reference_id=sales_id)
        self.assertEqual(entry.entry_type, 'DEBIT')
        self.assertEqual(entry.customer_id, self.customer.id)

    def test_insufficient_stock_blocks_confirmation(self):
        sales_id = self._create_draft()
        self._add_item(sales_id, quantity='1000', rate='80')
        resp = self._confirm(sales_id, '94400')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.current_stock, Decimal('100.000'))
        self.assertEqual(Sales.objects.get(id=sales_id).status, 'DRAFT')

    def test_duplicate_confirmation_is_a_noop(self):
        sales_id = self._create_draft()
        self._add_item(sales_id, quantity='10', rate='80')
        self._confirm(sales_id, '944')

        resp = self.client.patch(f'/api/sales/{sales_id}/', {'status': 'CONFIRMED'}, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.current_stock, Decimal('90.000'))
        self.assertEqual(Ledger.objects.filter(reference_type='SALES', reference_id=sales_id).count(), 1)

    def test_cancel_restores_stock_and_posts_reversal(self):
        sales_id = self._create_draft()
        self._add_item(sales_id, quantity='10', rate='80')
        self._confirm(sales_id, '944')

        resp = self.client.patch(f'/api/sales/{sales_id}/', {'status': 'CANCELLED'}, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.current_stock, Decimal('100.000'))

        entries = Ledger.objects.filter(reference_type='SALES', reference_id=sales_id).order_by('id')
        self.assertEqual(entries.count(), 2)
        original, reversal = entries
        self.assertEqual(original.entry_type, 'DEBIT')
        self.assertEqual(reversal.entry_type, 'CREDIT')
        original.refresh_from_db()
        self.assertEqual(original.amount, Decimal('944.00'))

    def test_cancellation_blocked_by_active_dispatch(self):
        sales_id = self._create_draft()
        self._add_item(sales_id, quantity='10', rate='80')
        self._confirm(sales_id, '944')

        Dispatch.objects.create(dispatch_number='SAL-DSP-001', sales_id=sales_id, dispatch_date='2026-01-02', status='DISPATCHED')

        resp = self.client.patch(f'/api/sales/{sales_id}/', {'status': 'CANCELLED'}, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Sales.objects.get(id=sales_id).status, 'CONFIRMED')

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.current_stock, Decimal('90.000'))

    def test_confirmed_sales_items_cannot_be_edited_or_deleted(self):
        sales_id = self._create_draft()
        item = self._add_item(sales_id, quantity='10', rate='80')
        self._confirm(sales_id, '944')

        edit = self.client.patch(f'/api/sales/sales-items/{item["id"]}/', {'quantity': '5'}, format='json', **auth_headers(self.manager))
        self.assertEqual(edit.status_code, status.HTTP_400_BAD_REQUEST)

        delete = self.client.delete(f'/api/sales/sales-items/{item["id"]}/', **auth_headers(self.manager))
        self.assertEqual(delete.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_sales_number_rejected(self):
        self._create_draft(sales_number='SAL-DUP-001')
        resp = self.client.post('/api/sales/', {
            'sales_number': 'SAL-DUP-001', 'customer': self.customer.id, 'sales_date': '2026-01-01',
            'status': 'DRAFT', 'total_amount': '0', 'gst_amount': '0', 'grand_total': '0',
        }, format='json', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class SalesConcurrencyTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('sal_conc_admin')
        self.customer = Customer.objects.create(customer_name='Conc Customer', customer_code='SALCONCCUS01')

    def _make_confirmable_draft(self, sales_number, material, quantity):
        sales = Sales.objects.create(
            sales_number=sales_number, customer=self.customer, sales_date='2026-01-01',
            status='DRAFT', total_amount=0, gst_amount=0, grand_total=0,
        )
        SalesItem.objects.create(
            sales=sales, material=material, quantity=quantity, unit='PCS', rate=Decimal('80'),
            taxable_amount=quantity * 80, gst_percentage=18, gst_amount=quantity * Decimal('14.4'),
            line_total=quantity * Decimal('94.4'),
        )
        return sales

    def test_concurrent_oversubscribed_confirmations_no_overselling(self):
        """Two Sales for the same material together demand more than
        available stock - exactly one must succeed, the other must be
        rejected, and stock must never go negative."""
        material = make_material('SALCONCMAT01')
        Stock.objects.create(material=material, current_stock=Decimal('10'), available_stock=Decimal('10'))

        s1 = self._make_confirmable_draft('SALCONC-001', material, Decimal('8'))
        s2 = self._make_confirmable_draft('SALCONC-002', material, Decimal('8'))

        results = {}

        def confirm(key, sales):
            try:
                client = APIClient()
                resp = client.patch(f'/api/sales/{sales.id}/', {
                    'status': 'CONFIRMED', 'total_amount': '640', 'gst_amount': '0', 'grand_total': '640',
                }, format='json', **auth_headers(self.admin))
                results[key] = resp.status_code
            finally:
                connection.close()

        t1 = threading.Thread(target=confirm, args=('s1', s1))
        t2 = threading.Thread(target=confirm, args=('s2', s2))
        t1.start()
        t2.start()
        t1.join(timeout=15)
        t2.join(timeout=15)

        codes = sorted([results.get('s1'), results.get('s2')])
        self.assertEqual(codes, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

        stock = Stock.objects.get(material=material)
        self.assertEqual(stock.current_stock, Decimal('2.000'))
        self.assertGreaterEqual(stock.current_stock, Decimal('0'))
