import threading
from decimal import Decimal

from django.core.cache import cache
from django.db import IntegrityError, connection, transaction
from django.test import TransactionTestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from customer.models import Customer
from supplier.models import Supplier
from ledger.models import Ledger
from payment.models import Payment
from dms_test_helpers import make_admin, make_manager, make_staff, auth_headers


class PaymentWorkflowTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('pay_admin')
        self.manager = make_manager('pay_manager')
        self.staff = make_staff('pay_staff')
        self.customer = Customer.objects.create(
            customer_name='Pay Customer', customer_code='PAYCUS01',
            opening_balance=Decimal('1000'), opening_balance_type='DEBIT',
        )
        self.supplier = Supplier.objects.create(
            supplier_name='Pay Supplier', supplier_code='PAYSUP01',
            opening_balance=Decimal('1000'), opening_balance_type='CREDIT',
        )

    def test_staff_has_zero_access(self):
        resp = self.client.get('/api/payment/', **auth_headers(self.staff))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_payment_in_requires_customer_forbids_supplier(self):
        resp = self.client.post('/api/payment/', {
            'payment_number': 'PAY-001', 'payment_type': 'PAYMENT_IN', 'payment_date': '2026-01-01',
            'supplier': self.supplier.id, 'amount': '100',
        }, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_payment_out_requires_supplier_forbids_customer(self):
        resp = self.client.post('/api/payment/', {
            'payment_number': 'PAY-002', 'payment_type': 'PAYMENT_OUT', 'payment_date': '2026-01-01',
            'customer': self.customer.id, 'amount': '100',
        }, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_zero_and_negative_amount_rejected(self):
        for amount in ('0', '-50'):
            with self.subTest(amount=amount):
                resp = self.client.post('/api/payment/', {
                    'payment_number': f'PAY-AMT-{amount}', 'payment_type': 'PAYMENT_IN', 'payment_date': '2026-01-01',
                    'customer': self.customer.id, 'amount': amount,
                }, format='json', **auth_headers(self.manager))
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_payment_in_posts_credit_ledger_entry(self):
        resp = self.client.post('/api/payment/', {
            'payment_number': 'PAY-003', 'payment_type': 'PAYMENT_IN', 'payment_date': '2026-01-01',
            'customer': self.customer.id, 'amount': '400',
        }, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

        entry = Ledger.objects.get(reference_type='PAYMENT_IN', reference_id=resp.data['id'])
        self.assertEqual(entry.entry_type, 'CREDIT')
        self.assertEqual(entry.balance, Decimal('600.00'))

    def test_payment_out_posts_debit_ledger_entry(self):
        resp = self.client.post('/api/payment/', {
            'payment_number': 'PAY-004', 'payment_type': 'PAYMENT_OUT', 'payment_date': '2026-01-01',
            'supplier': self.supplier.id, 'amount': '400',
        }, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

        entry = Ledger.objects.get(reference_type='PAYMENT_OUT', reference_id=resp.data['id'])
        self.assertEqual(entry.entry_type, 'DEBIT')
        self.assertEqual(entry.balance, Decimal('600.00'))

    def test_overpayment_rejected_and_leaves_no_partial_state(self):
        resp = self.client.post('/api/payment/', {
            'payment_number': 'PAY-005', 'payment_type': 'PAYMENT_IN', 'payment_date': '2026-01-01',
            'customer': self.customer.id, 'amount': '999999',
        }, format='json', **auth_headers(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Payment.objects.filter(payment_number='PAY-005').exists())
        self.assertFalse(Ledger.objects.filter(customer=self.customer).exists())

    def test_duplicate_payment_number_rejected(self):
        self.client.post('/api/payment/', {
            'payment_number': 'PAY-DUP', 'payment_type': 'PAYMENT_IN', 'payment_date': '2026-01-01',
            'customer': self.customer.id, 'amount': '100',
        }, format='json', **auth_headers(self.manager))
        dup = self.client.post('/api/payment/', {
            'payment_number': 'PAY-DUP', 'payment_type': 'PAYMENT_IN', 'payment_date': '2026-01-01',
            'customer': self.customer.id, 'amount': '50',
        }, format='json', **auth_headers(self.manager))
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancellation_posts_reversal_without_mutating_original(self):
        created = self.client.post('/api/payment/', {
            'payment_number': 'PAY-006', 'payment_type': 'PAYMENT_IN', 'payment_date': '2026-01-01',
            'customer': self.customer.id, 'amount': '300',
        }, format='json', **auth_headers(self.manager))
        payment_id = created.data['id']

        cancel = self.client.patch(f'/api/payment/{payment_id}/', {'status': 'CANCELLED'}, format='json', **auth_headers(self.manager))
        self.assertEqual(cancel.status_code, status.HTTP_200_OK, cancel.data)

        entries = Ledger.objects.filter(reference_type='PAYMENT_IN', reference_id=payment_id).order_by('id')
        self.assertEqual(entries.count(), 2)
        original, reversal = entries
        self.assertEqual(original.entry_type, 'CREDIT')
        self.assertEqual(original.amount, Decimal('300.00'))
        self.assertEqual(reversal.entry_type, 'DEBIT')

    def test_duplicate_cancellation_does_not_double_reverse(self):
        created = self.client.post('/api/payment/', {
            'payment_number': 'PAY-007', 'payment_type': 'PAYMENT_IN', 'payment_date': '2026-01-01',
            'customer': self.customer.id, 'amount': '300',
        }, format='json', **auth_headers(self.manager))
        payment_id = created.data['id']
        self.client.patch(f'/api/payment/{payment_id}/', {'status': 'CANCELLED'}, format='json', **auth_headers(self.manager))

        # Cancelled payments cannot change status again (serializer guard).
        resp = self.client.patch(f'/api/payment/{payment_id}/', {'status': 'CANCELLED'}, format='json', **auth_headers(self.manager))
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST))
        self.assertEqual(Ledger.objects.filter(reference_type='PAYMENT_IN', reference_id=payment_id, entry_type='DEBIT').count(), 1)

    def test_hard_delete_is_blocked(self):
        created = self.client.post('/api/payment/', {
            'payment_number': 'PAY-008', 'payment_type': 'PAYMENT_IN', 'payment_date': '2026-01-01',
            'customer': self.customer.id, 'amount': '100',
        }, format='json', **auth_headers(self.manager))
        payment_id = created.data['id']

        resp = self.client.delete(f'/api/payment/{payment_id}/', **auth_headers(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Payment.objects.filter(id=payment_id).exists())

    def test_customer_and_supplier_both_set_rejected_at_db_level(self):
        """DB-level CheckConstraint mirroring PaymentSerializer's XOR rule -
        a direct ORM write bypassing the serializer must still be blocked."""
        payment = Payment(
            payment_number='PAY-XOR-BAD', payment_type='PAYMENT_IN', payment_date='2026-01-01',
            customer=self.customer, supplier=self.supplier, amount=100,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                payment.save()

    def test_neither_customer_nor_supplier_rejected_at_db_level(self):
        payment = Payment(
            payment_number='PAY-XOR-BAD2', payment_type='PAYMENT_IN', payment_date='2026-01-01',
            amount=100,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                payment.save()


class PaymentConcurrencyTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin('pay_conc_admin')

    def _run_concurrent(self, path_and_payloads):
        results = {}

        def post(key, payload):
            try:
                client = APIClient()
                resp = client.post('/api/payment/', payload, format='json', **auth_headers(self.admin))
                results[key] = resp.status_code
            finally:
                connection.close()

        threads = [threading.Thread(target=post, args=(key, payload)) for key, payload in path_and_payloads]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)
        return results

    def test_concurrent_customer_payments_no_lost_update(self):
        customer = Customer.objects.create(customer_name='Conc Pay Customer', customer_code='PAYCONCCUS01', opening_balance=Decimal('1000'), opening_balance_type='DEBIT')
        results = self._run_concurrent([
            ('c1', {'payment_number': 'PAYCONC-001', 'payment_type': 'PAYMENT_IN', 'payment_date': '2026-01-01', 'customer': customer.id, 'amount': '300'}),
            ('c2', {'payment_number': 'PAYCONC-002', 'payment_type': 'PAYMENT_IN', 'payment_date': '2026-01-01', 'customer': customer.id, 'amount': '200'}),
        ])
        self.assertEqual(results['c1'], status.HTTP_201_CREATED)
        self.assertEqual(results['c2'], status.HTTP_201_CREATED)

        # Opening balance 1000 DEBIT, two Payment-In of 300/200 each reduce
        # the customer's outstanding balance: whichever posts first lands
        # at 700 or 800, and the final cumulative (whichever posts second)
        # is always 500 - the smallest value, since DEBIT decreases here.
        entries = Ledger.objects.filter(customer=customer).order_by('id')
        self.assertEqual(entries.count(), 2)
        balances = sorted(e.balance for e in entries)
        self.assertEqual(balances[0], Decimal('500.00'))
        self.assertIn(balances[1], [Decimal('700.00'), Decimal('800.00')])

    def test_concurrent_supplier_payments_no_lost_update(self):
        supplier = Supplier.objects.create(supplier_name='Conc Pay Supplier', supplier_code='PAYCONCSUP01', opening_balance=Decimal('1000'), opening_balance_type='CREDIT')
        results = self._run_concurrent([
            ('s1', {'payment_number': 'PAYCONC-003', 'payment_type': 'PAYMENT_OUT', 'payment_date': '2026-01-01', 'supplier': supplier.id, 'amount': '300'}),
            ('s2', {'payment_number': 'PAYCONC-004', 'payment_type': 'PAYMENT_OUT', 'payment_date': '2026-01-01', 'supplier': supplier.id, 'amount': '200'}),
        ])
        self.assertEqual(results['s1'], status.HTTP_201_CREATED)
        self.assertEqual(results['s2'], status.HTTP_201_CREATED)

        # Same reasoning as the customer case: opening 1000 CREDIT, two
        # Payment-Out of 300/200 each reduce the supplier's payable balance.
        entries = Ledger.objects.filter(supplier=supplier).order_by('id')
        self.assertEqual(entries.count(), 2)
        balances = sorted(e.balance for e in entries)
        self.assertEqual(balances[0], Decimal('500.00'))
        self.assertIn(balances[1], [Decimal('700.00'), Decimal('800.00')])
