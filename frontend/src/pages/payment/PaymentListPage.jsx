import { useEffect, useMemo, useState } from 'react';
import client from '../../api/client';
import usePaginatedList from '../../hooks/usePaginatedList';
import DataTable from '../../components/DataTable';
import ErrorBanner, { extractErrorMessage } from '../../components/ErrorBanner';
import StatusBadge from '../../components/StatusBadge';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';
import Pagination from '../../components/Pagination';

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

const PAYMENT_MODES = ['CASH', 'BANK_TRANSFER', 'CHEQUE', 'UPI', 'OTHER'];

const emptyForm = {
  payment_number: '', payment_type: 'PAYMENT_IN', payment_date: todayStr(),
  customer: '', supplier: '', amount: '', payment_mode: 'CASH', reference_number: '', remarks: '',
};

export default function PaymentListPage() {
  const [customers, setCustomers] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [typeFilter, setTypeFilter] = useState('');

  const filters = useMemo(() => (typeFilter ? { payment_type: typeFilter } : {}), [typeFilter]);
  const { rows, count, loading, error: listError, page, setPage, totalPages, reload } = usePaginatedList('/payment/', { filters });

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState(null);
  const [saving, setSaving] = useState(false);

  const [cancelTarget, setCancelTarget] = useState(null);
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState(null);

  const customerMap = Object.fromEntries(customers.map((c) => [c.id, c.customer_name]));
  const supplierMap = Object.fromEntries(suppliers.map((s) => [s.id, s.supplier_name]));

  useEffect(() => {
    Promise.all([
      client.get('/customer/', { params: { page_size: 200 } }),
      client.get('/supplier/', { params: { page_size: 200 } }),
    ]).then(([custResp, supResp]) => {
      setCustomers(custResp.data.results);
      setSuppliers(supResp.data.results);
    }).catch(() => { setCustomers([]); setSuppliers([]); });
  }, []);

  const openCreate = () => {
    setForm(emptyForm);
    setFormError(null);
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const payload = {
        payment_number: form.payment_number,
        payment_type: form.payment_type,
        payment_date: form.payment_date,
        amount: form.amount,
        payment_mode: form.payment_mode || undefined,
        reference_number: form.reference_number || undefined,
        remarks: form.remarks || undefined,
      };
      if (form.payment_type === 'PAYMENT_IN') {
        payload.customer = form.customer;
      } else {
        payload.supplier = form.supplier;
      }
      await client.post('/payment/', payload);
      setModalOpen(false);
      reload();
    } catch (err) {
      setFormError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = async () => {
    setCancelling(true);
    setCancelError(null);
    try {
      await client.patch(`/payment/${cancelTarget.id}/`, { status: 'CANCELLED' });
      setCancelTarget(null);
      reload();
    } catch (err) {
      setCancelError(extractErrorMessage(err));
    } finally {
      setCancelling(false);
    }
  };

  const columns = [
    { key: 'payment_number', header: 'Payment #' },
    { key: 'payment_type', header: 'Type' },
    { key: 'party', header: 'Party', render: (r) => (r.customer ? customerMap[r.customer] : supplierMap[r.supplier]) || '-' },
    { key: 'payment_date', header: 'Date' },
    { key: 'amount', header: 'Amount' },
    { key: 'payment_mode', header: 'Mode' },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    {
      key: '_actions',
      header: 'Actions',
      render: (r) => r.status === 'CONFIRMED'
        ? <button className="btn btn-danger btn-sm" onClick={() => setCancelTarget(r)}>Cancel</button>
        : null,
    },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Payments</h1>
        <button className="btn btn-primary" onClick={openCreate}>+ New Payment</button>
      </div>

      <ErrorBanner error={listError} />

      <div className="filters-bar">
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">All types</option>
          <option value="PAYMENT_IN">Payment In</option>
          <option value="PAYMENT_OUT">Payment Out</option>
        </select>
      </div>

      <DataTable columns={columns} rows={rows} loading={loading} emptyMessage="No payments found." />
      <Pagination page={page} totalPages={totalPages} count={count} onPageChange={setPage} />

      {modalOpen && (
        <Modal title="New Payment" onClose={() => setModalOpen(false)}>
          <form onSubmit={handleSubmit}>
            <ErrorBanner message={formError} />
            <div className="form-grid">
              <div className="form-field">
                <label>Payment Number *</label>
                <input required value={form.payment_number} onChange={(e) => setForm((p) => ({ ...p, payment_number: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Payment Type *</label>
                <select value={form.payment_type} onChange={(e) => setForm((p) => ({ ...p, payment_type: e.target.value }))}>
                  <option value="PAYMENT_IN">Payment In (from Customer)</option>
                  <option value="PAYMENT_OUT">Payment Out (to Supplier)</option>
                </select>
              </div>
              {form.payment_type === 'PAYMENT_IN' ? (
                <div className="form-field">
                  <label>Customer *</label>
                  <select required value={form.customer} onChange={(e) => setForm((p) => ({ ...p, customer: e.target.value }))}>
                    <option value="">-- Select --</option>
                    {customers.map((c) => <option key={c.id} value={c.id}>{c.customer_name}</option>)}
                  </select>
                </div>
              ) : (
                <div className="form-field">
                  <label>Supplier *</label>
                  <select required value={form.supplier} onChange={(e) => setForm((p) => ({ ...p, supplier: e.target.value }))}>
                    <option value="">-- Select --</option>
                    {suppliers.map((s) => <option key={s.id} value={s.id}>{s.supplier_name}</option>)}
                  </select>
                </div>
              )}
              <div className="form-field">
                <label>Payment Date *</label>
                <input type="date" required value={form.payment_date} onChange={(e) => setForm((p) => ({ ...p, payment_date: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Amount *</label>
                <input type="number" step="0.01" required value={form.amount} onChange={(e) => setForm((p) => ({ ...p, amount: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Payment Mode</label>
                <select value={form.payment_mode} onChange={(e) => setForm((p) => ({ ...p, payment_mode: e.target.value }))}>
                  {PAYMENT_MODES.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div className="form-field">
                <label>Reference Number</label>
                <input value={form.reference_number} onChange={(e) => setForm((p) => ({ ...p, reference_number: e.target.value }))} />
              </div>
            </div>
            <div className="form-field" style={{ marginTop: 14 }}>
              <label>Remarks</label>
              <textarea rows={2} value={form.remarks} onChange={(e) => setForm((p) => ({ ...p, remarks: e.target.value }))} />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setModalOpen(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save Payment'}</button>
            </div>
          </form>
        </Modal>
      )}

      {cancelTarget && (
        <ConfirmDialog
          title="Cancel Payment"
          message={cancelError || `Cancel payment "${cancelTarget.payment_number}"? This posts a reversing Ledger entry.`}
          confirmLabel="Cancel Payment"
          danger
          busy={cancelling}
          onConfirm={handleCancel}
          onCancel={() => { setCancelTarget(null); setCancelError(null); }}
        />
      )}
    </div>
  );
}
