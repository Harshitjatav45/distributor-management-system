import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../../api/client';
import ErrorBanner, { extractErrorMessage } from '../../components/ErrorBanner';

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

export default function PurchaseCreatePage() {
  const navigate = useNavigate();
  const [suppliers, setSuppliers] = useState([]);
  const [form, setForm] = useState({
    purchase_number: '',
    supplier: '',
    purchase_date: todayStr(),
    invoice_number: '',
    invoice_date: '',
    due_date: '',
    transport_name: '',
    vehicle_number: '',
    lr_number: '',
    received_by: '',
    remarks: '',
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    client.get('/supplier/').then((r) => setSuppliers(r.data)).catch(() => setSuppliers([]));
  }, []);

  const handleChange = (name, value) => setForm((p) => ({ ...p, [name]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = { ...form, status: 'DRAFT', total_amount: 0, gst_amount: 0, grand_total: 0, discount_amount: 0, round_off: 0 };
      for (const key of ['invoice_number', 'invoice_date', 'due_date', 'transport_name', 'vehicle_number', 'lr_number', 'received_by', 'remarks']) {
        if (payload[key] === '') delete payload[key];
      }
      const resp = await client.post('/purchase/', payload);
      navigate(`/purchases/${resp.data.id}`, { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>New Purchase</h1>
      </div>
      <div className="card" style={{ padding: 20 }}>
        <form onSubmit={handleSubmit}>
          <ErrorBanner message={error} />
          <div className="form-grid">
            <div className="form-field">
              <label>Purchase Number *</label>
              <input required value={form.purchase_number} onChange={(e) => handleChange('purchase_number', e.target.value)} />
            </div>
            <div className="form-field">
              <label>Supplier *</label>
              <select required value={form.supplier} onChange={(e) => handleChange('supplier', e.target.value)}>
                <option value="">-- Select --</option>
                {suppliers.map((s) => <option key={s.id} value={s.id}>{s.supplier_name}</option>)}
              </select>
            </div>
            <div className="form-field">
              <label>Purchase Date *</label>
              <input type="date" required value={form.purchase_date} onChange={(e) => handleChange('purchase_date', e.target.value)} />
            </div>
            <div className="form-field">
              <label>Invoice Number</label>
              <input value={form.invoice_number} onChange={(e) => handleChange('invoice_number', e.target.value)} />
            </div>
            <div className="form-field">
              <label>Invoice Date</label>
              <input type="date" value={form.invoice_date} onChange={(e) => handleChange('invoice_date', e.target.value)} />
            </div>
            <div className="form-field">
              <label>Due Date</label>
              <input type="date" value={form.due_date} onChange={(e) => handleChange('due_date', e.target.value)} />
            </div>
            <div className="form-field">
              <label>Transport Name</label>
              <input value={form.transport_name} onChange={(e) => handleChange('transport_name', e.target.value)} />
            </div>
            <div className="form-field">
              <label>Vehicle Number</label>
              <input value={form.vehicle_number} onChange={(e) => handleChange('vehicle_number', e.target.value)} />
            </div>
            <div className="form-field">
              <label>LR Number</label>
              <input value={form.lr_number} onChange={(e) => handleChange('lr_number', e.target.value)} />
            </div>
            <div className="form-field">
              <label>Received By</label>
              <input value={form.received_by} onChange={(e) => handleChange('received_by', e.target.value)} />
            </div>
          </div>
          <div className="form-field" style={{ marginTop: 14 }}>
            <label>Remarks</label>
            <textarea rows={2} value={form.remarks} onChange={(e) => handleChange('remarks', e.target.value)} />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/purchases')}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating...' : 'Create Draft'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
