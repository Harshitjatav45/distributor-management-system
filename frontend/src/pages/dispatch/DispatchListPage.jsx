import { useEffect, useMemo, useState } from 'react';
import client from '../../api/client';
import DataTable from '../../components/DataTable';
import ErrorBanner, { extractErrorMessage } from '../../components/ErrorBanner';
import StatusBadge from '../../components/StatusBadge';
import Modal from '../../components/Modal';

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

const VALID_TRANSITIONS = {
  DISPATCHED: ['OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED', 'CANCELLED'],
  OUT_FOR_DELIVERY: ['DELIVERED', 'FAILED', 'CANCELLED'],
  FAILED: ['OUT_FOR_DELIVERY', 'CANCELLED'],
  DELIVERED: [],
  CANCELLED: [],
};

const emptyForm = {
  dispatch_number: '', sales: '', dispatch_date: todayStr(),
  transport_name: '', vehicle_number: '', lr_number: '', delivery_person: '',
  delivery_address: '', expected_delivery_date: '', remarks: '',
};

export default function DispatchListPage() {
  const [rows, setRows] = useState([]);
  const [salesList, setSalesList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState(null);
  const [saving, setSaving] = useState(false);

  const [statusTarget, setStatusTarget] = useState(null);
  const [newStatus, setNewStatus] = useState('');
  const [statusError, setStatusError] = useState(null);
  const [statusSaving, setStatusSaving] = useState(false);

  const salesMap = Object.fromEntries(salesList.map((s) => [s.id, s.sales_number]));

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [dispResp, salesResp] = await Promise.all([client.get('/dispatch/'), client.get('/sales/')]);
      setRows(dispResp.data);
      setSalesList(salesResp.data.filter((s) => s.status === 'CONFIRMED'));
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const sortedRows = useMemo(() => [...rows].sort((a, b) => b.id - a.id), [rows]);

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
      const payload = { ...form };
      for (const key of ['transport_name', 'vehicle_number', 'lr_number', 'delivery_person', 'delivery_address', 'expected_delivery_date', 'remarks']) {
        if (payload[key] === '') delete payload[key];
      }
      await client.post('/dispatch/', payload);
      setModalOpen(false);
      await load();
    } catch (err) {
      setFormError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const openStatusUpdate = (row) => {
    setStatusTarget(row);
    setNewStatus('');
    setStatusError(null);
  };

  const handleStatusSubmit = async (e) => {
    e.preventDefault();
    setStatusSaving(true);
    setStatusError(null);
    try {
      await client.patch(`/dispatch/${statusTarget.id}/`, { status: newStatus });
      setStatusTarget(null);
      await load();
    } catch (err) {
      setStatusError(extractErrorMessage(err));
    } finally {
      setStatusSaving(false);
    }
  };

  const columns = [
    { key: 'dispatch_number', header: 'Dispatch #' },
    { key: 'sales', header: 'Sales #', render: (r) => salesMap[r.sales] || `#${r.sales}` },
    { key: 'dispatch_date', header: 'Dispatch Date' },
    { key: 'transport_name', header: 'Transport', render: (r) => r.transport_name || '-' },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    {
      key: '_actions',
      header: 'Actions',
      render: (r) => VALID_TRANSITIONS[r.status]?.length > 0
        ? <button className="btn btn-secondary btn-sm" onClick={() => openStatusUpdate(r)}>Update Status</button>
        : null,
    },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Dispatch</h1>
        <button className="btn btn-primary" onClick={openCreate}>+ New Dispatch</button>
      </div>

      <ErrorBanner error={error} />

      <DataTable columns={columns} rows={sortedRows} loading={loading} emptyMessage="No dispatches found." />

      {modalOpen && (
        <Modal title="New Dispatch" onClose={() => setModalOpen(false)} wide>
          <form onSubmit={handleSubmit}>
            <ErrorBanner message={formError} />
            <div className="form-grid">
              <div className="form-field">
                <label>Dispatch Number *</label>
                <input required value={form.dispatch_number} onChange={(e) => setForm((p) => ({ ...p, dispatch_number: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Sales Order (Confirmed only) *</label>
                <select required value={form.sales} onChange={(e) => setForm((p) => ({ ...p, sales: e.target.value }))}>
                  <option value="">-- Select --</option>
                  {salesList.map((s) => <option key={s.id} value={s.id}>{s.sales_number}</option>)}
                </select>
              </div>
              <div className="form-field">
                <label>Dispatch Date *</label>
                <input type="date" required value={form.dispatch_date} onChange={(e) => setForm((p) => ({ ...p, dispatch_date: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Transport Name</label>
                <input value={form.transport_name} onChange={(e) => setForm((p) => ({ ...p, transport_name: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Vehicle Number</label>
                <input value={form.vehicle_number} onChange={(e) => setForm((p) => ({ ...p, vehicle_number: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>LR Number</label>
                <input value={form.lr_number} onChange={(e) => setForm((p) => ({ ...p, lr_number: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Delivery Person</label>
                <input value={form.delivery_person} onChange={(e) => setForm((p) => ({ ...p, delivery_person: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Expected Delivery Date</label>
                <input type="date" value={form.expected_delivery_date} onChange={(e) => setForm((p) => ({ ...p, expected_delivery_date: e.target.value }))} />
              </div>
            </div>
            <div className="form-field" style={{ marginTop: 14 }}>
              <label>Delivery Address (blank = use customer address)</label>
              <textarea rows={2} value={form.delivery_address} onChange={(e) => setForm((p) => ({ ...p, delivery_address: e.target.value }))} />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setModalOpen(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Create Dispatch'}</button>
            </div>
          </form>
        </Modal>
      )}

      {statusTarget && (
        <Modal title={`Update Status - ${statusTarget.dispatch_number}`} onClose={() => setStatusTarget(null)}>
          <form onSubmit={handleStatusSubmit}>
            <ErrorBanner message={statusError} />
            <div className="form-field">
              <label>New Status</label>
              <select required value={newStatus} onChange={(e) => setNewStatus(e.target.value)}>
                <option value="">-- Select --</option>
                {(VALID_TRANSITIONS[statusTarget.status] || []).map((s) => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setStatusTarget(null)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={statusSaving}>{statusSaving ? 'Saving...' : 'Update'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
