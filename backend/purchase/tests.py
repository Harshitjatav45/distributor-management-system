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
from supplier.models import Supplier
from stock.models import Stock
from ledger.models import Ledger
from purchase.models import Purchase, PurchaseItem
from dms_test_helpers import make_admin, make_manager, make_staff, auth_headers


def make_material(code='PURMAT01'):
    company = Company.objects.create(company_name=f'PurCo {code}', company_code=f'PURCO-{code}')
    category = Category.objects.create(category_name=f'PurCat {code}')
    return Material.objects.create(
        material_name=f'Material {code}', material_code=code,
        company=company, category=category,
        mrp=100, purchase_price=50, selling_price=80, gst_percentage=18,
    )


class PurchaseWorkflowTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('pur_admin')
        self.manager = make_manager('pur_manager')
        self.staff = make_staff('pur_staff')
        self.supplier = Supplier.objects.create(supplier_name='Pur Supplier', supplier_code='PURSUP01')
        self.material = make_material('PURMAT01')

    def _create_draft(self, user=None, purchase_number='PUR-TEST-001'):
        user = user or self.staff
        resp = self.client.post('/api/purchase/', {
            'purchase_number': purchase_number, 'supplier': self.supplier.id, 'purchase_date': '2026-01-01',
            'status': 'DRAFT', 'total_amount': '0', 'gst_amount': '0', 'grand_total': '0',
        }, format='json', **auth_headers(user))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        return resp.data['id']

    def _add_item(self, purchase_id, quantity='10', rate='50', gst_percentage='18', user=None):
        user = user or self.staff
        resp = self.client.post('/api/purchase/purchase-items/', {
            'purchase': purchase_id, 'material': self.material.id, 'quantity': quantity,
            'unit': 'PCS', 'rate': rate, 'gst_percentage': gst_percentage,
            'taxable_amount': str(Decimal(quantity) * Decimal(rate)),
            'gst_amount': str(Decimal(quantity) * Decimal(rate) * Decimal(gst_percentage) / 100),
            'line_total': str(Decimal(quantity) * Decimal(rate) * (1 + Decimal(gst_percentage) / 100)),
        }, format='json', **auth_headers(user))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        return resp.data

    def _confirm(self, purchase_id, grand_total, user=None):
        user = user or self.manager
        return self.client.patch(f'/api/purchase/{purchase_id}/', {
            'status': 'CONFIRMED', 'total_amount': '500', 'gst_amount': '90', 'grand_total': str(grand_total),
        }, format='json', **auth_headers(user))

    def test_staff_can_create_draft_and_add_items(self):
        purchase_id = self._create_draft()
        self._add_item(purchase_id)
        items = PurchaseItem.objects.filter(purchase_id=purchase_id)
        self.assertEqual(items.count(), 1)

    def test_staff_cannot_confirm(self):
        purchase_id = self._create_draft()
        self._add_item(purchase_id)
        resp = self._confirm(purchase_id, '590', user=self.staff)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_confirm_increases_stock_and_posts_ledger(self):
        Stock.objects.create(material=self.material, current_stock=0, available_stock=0)
        purchase_id = self._create_draft()
        self._add_item(purchase_id, quantity='10', rate='50')

        resp = self._confirm(purchase_id, '590')
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

        stock = Stock.objects.get(material=self.material)
        self.assertEqual(stock.current_stock, Decimal('10.000'))
        self.assertEqual(stock.available_stock, Decimal('10.000'))

        ledger_entry = Ledger.objects.get(reference_type='PURCHASE', reference_id=purchase_id)
        self.assertEqual(ledger_entry.entry_type, 'CREDIT')
        self.assertEqual(ledger_entry.supplier_id, self.supplier.id)

    def test_zero_grand_total_blocks_confirmation(self):
        purchase_id = self._create_draft()
        self._add_item(purchase_id)
        resp = self.client.patch(f'/api/purchase/{purchase_id}/', {'status': 'CONFIRMED'}, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Purchase.objects.get(id=purchase_id).status, 'DRAFT')

    def test_duplicate_confirmation_is_a_noop_not_double_posted(self):
        Stock.objects.create(material=self.material, current_stock=0, available_stock=0)
        purchase_id = self._create_draft()
        self._add_item(purchase_id)
        self._confirm(purchase_id, '590')

        # Re-saving with status already CONFIRMED must not re-trigger the
        # stock/ledger side effects a second time.
        resp = self.client.patch(f'/api/purchase/{purchase_id}/', {'status': 'CONFIRMED'}, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        stock = Stock.objects.get(material=self.material)
        self.assertEqual(stock.current_stock, Decimal('10.000'))
        self.assertEqual(Ledger.objects.filter(reference_type='PURCHASE', reference_id=purchase_id).count(), 1)

    def test_cancel_reverses_stock_and_posts_offsetting_ledger_entry(self):
        Stock.objects.create(material=self.material, current_stock=0, available_stock=0)
        purchase_id = self._create_draft()
        self._add_item(purchase_id)
        self._confirm(purchase_id, '590')

        resp = self.client.patch(f'/api/purchase/{purchase_id}/', {'status': 'CANCELLED'}, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

        stock = Stock.objects.get(material=self.material)
        self.assertEqual(stock.current_stock, Decimal('0.000'))

        entries = Ledger.objects.filter(reference_type='PURCHASE', reference_id=purchase_id).order_by('id')
        self.assertEqual(entries.count(), 2)
        original, reversal = entries
        self.assertEqual(original.entry_type, 'CREDIT')
        self.assertEqual(original.amount, Decimal('590.00'))
        self.assertEqual(reversal.entry_type, 'DEBIT')
        self.assertEqual(reversal.amount, Decimal('590.00'))
        # Original entry must remain exactly as posted - never mutated.
        original.refresh_from_db()
        self.assertEqual(original.entry_type, 'CREDIT')
        self.assertEqual(original.amount, Decimal('590.00'))

    def test_cancellation_blocked_when_it_would_make_stock_negative(self):
        Stock.objects.create(material=self.material, current_stock=0, available_stock=0)
        purchase_id = self._create_draft()
        self._add_item(purchase_id, quantity='10', rate='50')
        self._confirm(purchase_id, '590')

        # Simulate external consumption of the stock this purchase brought in.
        stock = Stock.objects.get(material=self.material)
        stock.current_stock = Decimal('2')
        stock.available_stock = Decimal('2')
        stock.save()

        resp = self.client.patch(f'/api/purchase/{purchase_id}/', {'status': 'CANCELLED'}, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Rollback verification: purchase status and stock both unchanged.
        self.assertEqual(Purchase.objects.get(id=purchase_id).status, 'CONFIRMED')
        stock.refresh_from_db()
        self.assertEqual(stock.current_stock, Decimal('2.000'))
        self.assertEqual(Ledger.objects.filter(reference_type='PURCHASE', reference_id=purchase_id, entry_type='DEBIT').count(), 0)

    def test_cancelled_purchase_cannot_change_status_again(self):
        Stock.objects.create(material=self.material, current_stock=0, available_stock=0)
        purchase_id = self._create_draft()
        self._add_item(purchase_id)
        self._confirm(purchase_id, '590')
        self.client.patch(f'/api/purchase/{purchase_id}/', {'status': 'CANCELLED'}, format='json', **auth_headers(self.manager))

        resp = self.client.patch(f'/api/purchase/{purchase_id}/', {'status': 'DRAFT'}, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirmed_purchase_items_cannot_be_edited_or_deleted(self):
        Stock.objects.create(material=self.material, current_stock=0, available_stock=0)
        purchase_id = self._create_draft()
        item = self._add_item(purchase_id)
        self._confirm(purchase_id, '590')

        edit = self.client.patch(f'/api/purchase/purchase-items/{item["id"]}/', {'quantity': '99'}, format='json', **auth_headers(self.manager))
        self.assertEqual(edit.status_code, status.HTTP_400_BAD_REQUEST)

        delete = self.client.delete(f'/api/purchase/purchase-items/{item["id"]}/', **auth_headers(self.manager))
        self.assertEqual(delete.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_purchase_number_rejected(self):
        self._create_draft(purchase_number='PUR-DUP-001')
        resp = self.client.post('/api/purchase/', {
            'purchase_number': 'PUR-DUP-001', 'supplier': self.supplier.id, 'purchase_date': '2026-01-01',
            'status': 'DRAFT', 'total_amount': '0', 'gst_amount': '0', 'grand_total': '0',
        }, format='json', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_purchase_header_delete_is_admin_only(self):
        purchase_id = self._create_draft()
        self.assertEqual(self.client.delete(f'/api/purchase/{purchase_id}/', **auth_headers(self.manager)).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(f'/api/purchase/{purchase_id}/', **auth_headers(self.admin)).status_code, status.HTTP_204_NO_CONTENT)

    def test_list_endpoints_are_paginated(self):
        resp = self.client.get('/api/purchase/', **auth_headers(self.admin))
        self.assertEqual(set(resp.data.keys()), {'count', 'next', 'previous', 'results'})

    def test_status_query_param_filters_list(self):
        draft_id = self._create_draft(purchase_number='PUR-STATUS-DRAFT')
        confirmed_id = self._create_draft(purchase_number='PUR-STATUS-CONF')
        self._add_item(confirmed_id)
        self._confirm(confirmed_id, '590')

        draft_resp = self.client.get('/api/purchase/?status=DRAFT', **auth_headers(self.admin))
        draft_numbers = [row['purchase_number'] for row in draft_resp.data['results']]
        self.assertIn('PUR-STATUS-DRAFT', draft_numbers)
        self.assertNotIn('PUR-STATUS-CONF', draft_numbers)

        confirmed_resp = self.client.get('/api/purchase/?status=CONFIRMED', **auth_headers(self.admin))
        confirmed_numbers = [row['purchase_number'] for row in confirmed_resp.data['results']]
        self.assertIn('PUR-STATUS-CONF', confirmed_numbers)
        self.assertNotIn('PUR-STATUS-DRAFT', confirmed_numbers)

    def test_purchase_items_endpoint_filters_by_purchase_id(self):
        """Critical for pagination correctness: /purchase-items/ lists ALL
        items system-wide by default, so a client fetching just one
        purchase's items MUST filter server-side via ?purchase=<id> -
        otherwise items past page 1 of the global list would silently
        vanish from that purchase's detail view."""
        purchase_a = self._create_draft(purchase_number='PUR-FILTER-A')
        purchase_b = self._create_draft(purchase_number='PUR-FILTER-B')
        self._add_item(purchase_a)
        self._add_item(purchase_b)
        self._add_item(purchase_b)

        resp = self.client.get(f'/api/purchase/purchase-items/?purchase={purchase_b}', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 2)
        for item in resp.data['results']:
            self.assertEqual(item['purchase'], purchase_b)


class PurchaseConcurrencyTests(TransactionTestCase):
    """Uses TransactionTestCase (real commits, real separate DB connections
    per thread) rather than APITestCase, because select_for_update()
    row-locking can only be meaningfully exercised across genuinely
    concurrent transactions - APITestCase wraps each test in one shared,
    uncommitted transaction which would make this test meaningless.
    """
    def setUp(self):
        cache.clear()
        self.admin = make_admin('pur_conc_admin')
        self.supplier = Supplier.objects.create(supplier_name='Concurrency Supplier', supplier_code='CONCSUP01')

    def _make_confirmed_draft_purchase(self, purchase_number, material, quantity, rate):
        purchase = Purchase.objects.create(
            purchase_number=purchase_number, supplier=self.supplier, purchase_date='2026-01-01',
            status='DRAFT', total_amount=0, gst_amount=0, grand_total=0,
        )
        PurchaseItem.objects.create(
            purchase=purchase, material=material, quantity=quantity, unit='PCS', rate=rate,
            taxable_amount=quantity * rate, gst_percentage=18, gst_amount=quantity * rate * Decimal('0.18'),
            line_total=quantity * rate * Decimal('1.18'),
        )
        return purchase

    def test_concurrent_confirm_same_supplier_no_lost_update_on_balance(self):
        material = make_material('CONCMAT01')
        Stock.objects.create(material=material, current_stock=0, available_stock=0)
        p1 = self._make_confirmed_draft_purchase('CONC-PUR-001', material, Decimal('5'), Decimal('100'))
        p2 = self._make_confirmed_draft_purchase('CONC-PUR-002', material, Decimal('3'), Decimal('100'))

        results = {}

        def confirm(key, purchase, grand_total):
            try:
                client = APIClient()
                resp = client.patch(f'/api/purchase/{purchase.id}/', {
                    'status': 'CONFIRMED', 'total_amount': str(grand_total), 'gst_amount': '0', 'grand_total': str(grand_total),
                }, format='json', **auth_headers(self.admin))
                results[key] = resp.status_code
            finally:
                # Each thread gets its own DB connection; without an
                # explicit close, PostgreSQL sees this test database as
                # still "in use" when TransactionTestCase tries to flush/
                # tear it down after the test.
                connection.close()

        t1 = threading.Thread(target=confirm, args=('p1', p1, Decimal('500')))
        t2 = threading.Thread(target=confirm, args=('p2', p2, Decimal('300')))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(results['p1'], status.HTTP_200_OK)
        self.assertEqual(results['p2'], status.HTTP_200_OK)

        # Both stock deltas must be reflected - no lost update on the
        # shared Stock row despite concurrent select_for_update() locking.
        stock = Stock.objects.get(material=material)
        self.assertEqual(stock.current_stock, Decimal('8.000'))

        # Both ledger postings must be present with a consistent running
        # balance chain. Thread scheduling is non-deterministic, so either
        # p1 (500) or p2 (300) could post first - the only invariants that
        # must hold regardless of order are: the final cumulative balance
        # is the sum of both (800), and the earlier one is whichever
        # individual amount went first.
        entries = Ledger.objects.filter(supplier=self.supplier).order_by('id')
        self.assertEqual(entries.count(), 2)
        balances = sorted(e.balance for e in entries)
        self.assertEqual(balances[-1], Decimal('800.00'))
        self.assertIn(balances[0], [Decimal('300.00'), Decimal('500.00')])

    def test_concurrent_confirm_overlapping_materials_no_deadlock(self):
        """Two purchases sharing two overlapping materials, confirmed
        concurrently: this specifically exercises the deterministic
        material_id lock ordering fix in purchase/services.py - without it,
        two purchases locking the same two Stock rows in opposite orders
        can deadlock.
        """
        material_a = make_material('DEADLOCK-A')
        material_b = make_material('DEADLOCK-B')
        Stock.objects.create(material=material_a, current_stock=0, available_stock=0)
        Stock.objects.create(material=material_b, current_stock=0, available_stock=0)

        p1 = Purchase.objects.create(
            purchase_number='DEADLOCK-PUR-001', supplier=self.supplier, purchase_date='2026-01-01',
            status='DRAFT', total_amount=0, gst_amount=0, grand_total=0,
        )
        # p1 items inserted B then A (reverse of material_id order)
        for material, qty in [(material_b, Decimal('2')), (material_a, Decimal('2'))]:
            PurchaseItem.objects.create(
                purchase=p1, material=material, quantity=qty, unit='PCS', rate=Decimal('10'),
                taxable_amount=qty * 10, gst_percentage=18, gst_amount=qty * Decimal('1.8'), line_total=qty * Decimal('11.8'),
            )

        p2 = Purchase.objects.create(
            purchase_number='DEADLOCK-PUR-002', supplier=self.supplier, purchase_date='2026-01-01',
            status='DRAFT', total_amount=0, gst_amount=0, grand_total=0,
        )
        # p2 items inserted A then B
        for material, qty in [(material_a, Decimal('3')), (material_b, Decimal('3'))]:
            PurchaseItem.objects.create(
                purchase=p2, material=material, quantity=qty, unit='PCS', rate=Decimal('10'),
                taxable_amount=qty * 10, gst_percentage=18, gst_amount=qty * Decimal('1.8'), line_total=qty * Decimal('11.8'),
            )

        results = {}

        def confirm(key, purchase):
            try:
                client = APIClient()
                resp = client.patch(f'/api/purchase/{purchase.id}/', {
                    'status': 'CONFIRMED', 'total_amount': '100', 'gst_amount': '0', 'grand_total': '100',
                }, format='json', **auth_headers(self.admin))
                results[key] = resp.status_code
            finally:
                connection.close()

        t1 = threading.Thread(target=confirm, args=('p1', p1))
        t2 = threading.Thread(target=confirm, args=('p2', p2))
        t1.start()
        t2.start()
        t1.join(timeout=15)
        t2.join(timeout=15)

        self.assertFalse(t1.is_alive(), 'thread 1 appears to have deadlocked')
        self.assertFalse(t2.is_alive(), 'thread 2 appears to have deadlocked')
        self.assertEqual(results.get('p1'), status.HTTP_200_OK)
        self.assertEqual(results.get('p2'), status.HTTP_200_OK)

        stock_a = Stock.objects.get(material=material_a)
        stock_b = Stock.objects.get(material=material_b)
        self.assertEqual(stock_a.current_stock, Decimal('5.000'))
        self.assertEqual(stock_b.current_stock, Decimal('5.000'))
