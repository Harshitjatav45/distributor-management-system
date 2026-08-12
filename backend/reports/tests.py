from decimal import Decimal

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from company.models import Company
from category.models import Category
from material.models import Material
from stock.models import Stock
from customer.models import Customer
from supplier.models import Supplier
from ledger.models import Ledger
from dms_test_helpers import make_admin, make_manager, make_staff, auth_headers


class ReportsTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('rep_admin')
        self.manager = make_manager('rep_manager')
        self.staff = make_staff('rep_staff')

        company = Company.objects.create(company_name='Rep Co', company_code='REPCO01')
        category = Category.objects.create(category_name='Rep Cat')
        material = Material.objects.create(
            material_name='Rep Material', material_code='REPMAT01', company=company, category=category,
            mrp=100, purchase_price=50, selling_price=80, gst_percentage=18,
        )
        Stock.objects.create(material=material, current_stock=Decimal('42'), available_stock=Decimal('42'))

        self.customer = Customer.objects.create(customer_name='Rep Customer', customer_code='REPCUS01', opening_balance=Decimal('1000'), opening_balance_type='DEBIT')
        Ledger.objects.create(transaction_date='2026-01-01', reference_type='OPENING', customer=self.customer, entry_type='DEBIT', amount=Decimal('1000'), balance=Decimal('1000'))

        self.supplier = Supplier.objects.create(supplier_name='Rep Supplier', supplier_code='REPSUP01')

    def test_financial_reports_require_admin_or_manager(self):
        for path in ['/api/reports/purchase/', '/api/reports/sales/', '/api/reports/customers/', '/api/reports/suppliers/', '/api/reports/ledger/']:
            with self.subTest(path=path):
                staff_resp = self.client.get(path, **auth_headers(self.staff))
                self.assertEqual(staff_resp.status_code, status.HTTP_403_FORBIDDEN)
                admin_resp = self.client.get(path, **auth_headers(self.admin))
                self.assertEqual(admin_resp.status_code, status.HTTP_200_OK)
                manager_resp = self.client.get(path, **auth_headers(self.manager))
                self.assertEqual(manager_resp.status_code, status.HTTP_200_OK)

    def test_stock_report_open_to_all_roles(self):
        """Matches the approved RBAC design: Stock report is open to all
        authenticated roles, unlike the other five reports."""
        for user in (self.admin, self.manager, self.staff):
            with self.subTest(user=user.username):
                resp = self.client.get('/api/reports/stock/', **auth_headers(user))
                self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_stock_report_reflects_real_data(self):
        resp = self.client.get('/api/reports/stock/', **auth_headers(self.staff))
        names = [row['material__material_name'] for row in resp.data]
        self.assertIn('Rep Material', names)

    def test_customer_report_computes_outstanding_balance(self):
        resp = self.client.get('/api/reports/customers/', **auth_headers(self.admin))
        row = next(r for r in resp.data if r['id'] == self.customer.id)
        self.assertEqual(Decimal(row['outstanding_balance']), Decimal('1000.00'))

    def test_unauthenticated_rejected(self):
        resp = self.client.get('/api/reports/purchase/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
