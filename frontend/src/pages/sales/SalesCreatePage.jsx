import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../../api/client';
import ErrorBanner, { extractErrorMessage } from '../../components/ErrorBanner';

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

export default function SalesCreatePage() {
  const navigate = useNavigate();
  const [customers, setCustomers] = useState([]);
  const [form, setForm] = useState({
    sales_number: '',
    customer: '',
    sales_date: todayStr(),
    invoice_number: '',
    invoice_date: '',
    due_date: '',
    remarks: '',
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    client.get('/customer/', { params: { page_size: 200 } }).then((r) => setCustomers(r.data.results)).catch(() => setCustomers([]));
  }, []);

  const handleChange = (name, value) => setForm((p) => ({ ...p, [name]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = { ...form, status: 'DRAFT', total_amount: 0, gst_amount: 0, grand_total: 0, discount_amount: 0, round_off: 0 };
      for (const key of ['invoice_number', 'invoice_date', 'due_date', 'remarks']) {
        if (payload[key] === '') delete payload[key];
      }
      const resp = await client.post('/sales/', payload);
      navigate(`/sales/${resp.data.id}`, { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>New Sales Order</h1>
      </div>
      <div className="card" style={{ padding: 20 }}>
        <form onSubmit={handleSubmit}>
          <ErrorBanner message={error} />
          <div className="form-grid">
            <div className="form-field">
              <label>Sales Number *</label>
              <input required value={form.sales_number} onChange={(e) => handleChange('sales_number', e.target.value)} />
            </div>
            <div className="form-field">
              <label>Customer *</label>
              <select required value={form.customer} onChange={(e) => handleChange('customer', e.target.value)}>
                <option value="">-- Select --</option>
                {customers.map((c) => <option key={c.id} value={c.id}>{c.customer_name}</option>)}
              </select>
            </div>
            <div className="form-field">
              <label>Sales Date *</label>
              <input type="date" required value={form.sales_date} onChange={(e) => handleChange('sales_date', e.target.value)} />
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
          </div>
          <div className="form-field" style={{ marginTop: 14 }}>
            <label>Remarks</label>
            <textarea rows={2} value={form.remarks} onChange={(e) => handleChange('remarks', e.target.value)} />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/sales')}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating...' : 'Create Draft'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
