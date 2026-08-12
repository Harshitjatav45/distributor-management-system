from decimal import Decimal

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from company.models import Company
from category.models import Category
from material.models import Material
from supplier.models import Supplier
from stock.models import Stock
from purchase.models import Purchase, PurchaseItem
from audit.models import AuditLog
from dms_test_helpers import make_admin, make_manager, make_staff, auth_headers


class AuditLogPermissionTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('aud_admin')
        self.manager = make_manager('aud_manager')
        self.staff = make_staff('aud_staff')

    def test_only_admin_can_read(self):
        self.assertEqual(self.client.get('/api/audit/', **auth_headers(self.staff)).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get('/api/audit/', **auth_headers(self.manager)).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get('/api/audit/', **auth_headers(self.admin)).status_code, status.HTTP_200_OK)

    def test_writes_are_structurally_rejected(self):
        for method, kwargs in [
            ('post', {}), ('put', {}), ('patch', {}),
        ]:
            with self.subTest(method=method):
                resp = getattr(self.client, method)('/api/audit/', {}, format='json', **auth_headers(self.admin))
                self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete('/api/audit/', **auth_headers(self.admin)).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AuditLogCoverageTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('audcov_admin')
        self.manager = make_manager('audcov_manager')

    def test_master_data_create_and_delete_are_logged(self):
        created = self.client.post('/api/company/', {'company_name': 'Audit Co', 'company_code': 'AUDCO01'}, format='json', **auth_headers(self.admin))
        company_id = created.data['id']
        create_log = AuditLog.objects.filter(model_name='Company', action='CREATE', object_id=str(company_id)).first()
        self.assertIsNotNone(create_log)
        self.assertEqual(create_log.actor_username, 'audcov_admin')
        self.assertEqual(create_log.after_state['company_name'], 'Audit Co')

        self.client.patch(f'/api/company/{company_id}/', {'city': 'Jaipur'}, format='json', **auth_headers(self.admin))
        update_log = AuditLog.objects.filter(model_name='Company', action='UPDATE', object_id=str(company_id)).first()
        self.assertIsNotNone(update_log)
        self.assertEqual(update_log.after_state['city'], 'Jaipur')

        self.client.delete(f'/api/company/{company_id}/', **auth_headers(self.admin))
        delete_log = AuditLog.objects.filter(model_name='Company', action='DELETE', object_id=str(company_id)).first()
        self.assertIsNotNone(delete_log)
        self.assertEqual(delete_log.before_state['company_name'], 'Audit Co')

    def test_stock_write_is_logged(self):
        from company.models import Company as _Company
        from category.models import Category as _Category
        from material.models import Material as _Material
        from stock.models import Stock as _Stock

        company = _Company.objects.create(company_name='Stock Audit Co', company_code='STKAUDCO01')
        category = _Category.objects.create(category_name='Stock Audit Cat')
        material = _Material.objects.create(
            material_name='Stock Audit Material', material_code='STKAUDMAT01',
            company=company, category=category, mrp=100, purchase_price=50, selling_price=80, gst_percentage=18,
        )
        stock = _Stock.objects.create(material=material, current_stock=10, available_stock=10)

        self.client.patch(f'/api/stock/{stock.id}/', {'current_stock': '15', 'available_stock': '15'}, format='json', **auth_headers(self.admin))

        log = AuditLog.objects.filter(model_name='Stock', action='UPDATE', object_id=str(stock.id)).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.object_repr, 'Stock Audit Material')
        self.assertEqual(log.after_state['current_stock'], '15.000')

    def test_purchase_item_crud_is_logged(self):
        from supplier.models import Supplier as _Supplier
        from company.models import Company as _Company
        from category.models import Category as _Category
        from material.models import Material as _Material
        from purchase.models import Purchase as _Purchase

        supplier = _Supplier.objects.create(supplier_name='Item Audit Supplier', supplier_code='ITEMAUDSUP01')
        company = _Company.objects.create(company_name='Item Audit Co', company_code='ITEMAUDCO01')
        category = _Category.objects.create(category_name='Item Audit Cat')
        material = _Material.objects.create(
            material_name='Item Audit Material', material_code='ITEMAUDMAT01',
            company=company, category=category, mrp=100, purchase_price=50, selling_price=80, gst_percentage=18,
        )
        purchase = _Purchase.objects.create(
            purchase_number='ITEMAUD-PUR-001', supplier=supplier, purchase_date='2026-01-01',
            status='DRAFT', total_amount=0, gst_amount=0, grand_total=0,
        )

        created = self.client.post('/api/purchase/purchase-items/', {
            'purchase': purchase.id, 'material': material.id, 'quantity': '5', 'unit': 'PCS', 'rate': '50',
            'taxable_amount': '250', 'gst_percentage': '18', 'gst_amount': '45', 'line_total': '295',
        }, format='json', **auth_headers(self.admin))
        item_id = created.data['id']
        self.assertTrue(AuditLog.objects.filter(model_name='PurchaseItem', action='CREATE', object_id=str(item_id)).exists())

        self.client.patch(f'/api/purchase/purchase-items/{item_id}/', {'quantity': '10'}, format='json', **auth_headers(self.admin))
        self.assertTrue(AuditLog.objects.filter(model_name='PurchaseItem', action='UPDATE', object_id=str(item_id)).exists())

        self.client.delete(f'/api/purchase/purchase-items/{item_id}/', **auth_headers(self.admin))
        self.assertTrue(AuditLog.objects.filter(model_name='PurchaseItem', action='DELETE', object_id=str(item_id)).exists())

    def test_user_management_actions_are_logged_without_password_leakage(self):
        created = self.client.post('/api/users/', {
            'username': 'audcov_target', 'password': 'AuditedPass!234', 'group': 'Staff',
        }, format='json', **auth_headers(self.admin))
        user_id = created.data['id']

        self.client.patch(f'/api/users/{user_id}/', {'is_active': False}, format='json', **auth_headers(self.admin))
        self.client.post(f'/api/users/{user_id}/set-password/', {'new_password': 'NewAuditedPass!234'}, format='json', **auth_headers(self.admin))

        create_log = AuditLog.objects.get(model_name='User', action='CREATE', object_id=str(user_id))
        deactivate_log = AuditLog.objects.get(model_name='User', action='DEACTIVATE', object_id=str(user_id))
        password_log = AuditLog.objects.get(model_name='User', action='PASSWORD_CHANGE', object_id=str(user_id))

        for log in (create_log, deactivate_log, password_log):
            blob = f'{log.before_state}{log.after_state}{log.metadata}'
            self.assertNotIn('AuditedPass!234', blob)
            self.assertNotIn('NewAuditedPass!234', blob)

    def test_purchase_confirm_and_cancel_are_logged(self):
        supplier = Supplier.objects.create(supplier_name='Audit Supplier', supplier_code='AUDSUP01')
        company = Company.objects.create(company_name='Audit Mat Co', company_code='AUDMATCO01')
        category = Category.objects.create(category_name='Audit Cat')
        material = Material.objects.create(
            material_name='Audit Material', material_code='AUDMAT01', company=company, category=category,
            mrp=100, purchase_price=50, selling_price=80, gst_percentage=18,
        )
        Stock.objects.create(material=material, current_stock=0, available_stock=0)

        purchase = Purchase.objects.create(
            purchase_number='AUD-PUR-001', supplier=supplier, purchase_date='2026-01-01',
            status='DRAFT', total_amount=0, gst_amount=0, grand_total=0,
        )
        PurchaseItem.objects.create(
            purchase=purchase, material=material, quantity=Decimal('5'), unit='PCS', rate=Decimal('50'),
            taxable_amount=Decimal('250'), gst_percentage=18, gst_amount=Decimal('45'), line_total=Decimal('295'),
        )

        self.client.patch(f'/api/purchase/{purchase.id}/', {
            'status': 'CONFIRMED', 'total_amount': '250', 'gst_amount': '45', 'grand_total': '295',
        }, format='json', **auth_headers(self.manager))
        self.assertTrue(AuditLog.objects.filter(model_name='Purchase', action='CONFIRM', object_id=str(purchase.id)).exists())

        self.client.patch(f'/api/purchase/{purchase.id}/', {'status': 'CANCELLED'}, format='json', **auth_headers(self.manager))
        self.assertTrue(AuditLog.objects.filter(model_name='Purchase', action='CANCEL', object_id=str(purchase.id)).exists())

    def test_failed_transaction_leaves_no_orphan_audit_entry(self):
        """A confirm attempt that fails business validation must roll back
        atomically - including not leaving behind an AuditLog row for an
        action that never actually happened."""
        supplier = Supplier.objects.create(supplier_name='Rollback Supplier', supplier_code='ROLLSUP01')
        purchase = Purchase.objects.create(
            purchase_number='ROLL-PUR-001', supplier=supplier, purchase_date='2026-01-01',
            status='DRAFT', total_amount=0, gst_amount=0, grand_total=0,
        )

        before_count = AuditLog.objects.filter(model_name='Purchase', action='CONFIRM').count()

        # No items and grand_total=0 -> confirm_purchase() raises before
        # any stock/ledger/audit side effect is applied.
        resp = self.client.patch(f'/api/purchase/{purchase.id}/', {'status': 'CONFIRMED'}, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        after_count = AuditLog.objects.filter(model_name='Purchase', action='CONFIRM').count()
        self.assertEqual(before_count, after_count)
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, 'DRAFT')
