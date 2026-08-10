import { useEffect, useMemo, useState } from 'react';
import client from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import DataTable from '../../components/DataTable';
import ErrorBanner, { extractErrorMessage } from '../../components/ErrorBanner';
import Modal from '../../components/Modal';

export default function StockPage() {
  const { user } = useAuth();
  const canWrite = user?.role === 'Admin' || user?.role === 'Manager';

  const [stockRows, setStockRows] = useState([]);
  const [materials, setMaterials] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');

  const [editing, setEditing] = useState(null);
  const [formState, setFormState] = useState({});
  const [formError, setFormError] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [stockResp, materialResp] = await Promise.all([client.get('/stock/'), client.get('/material/')]);
      setStockRows(stockResp.data);
      const map = {};
      for (const m of materialResp.data) map[m.id] = m;
      setMaterials(map);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filteredRows = useMemo(() => {
    if (!search.trim()) return stockRows;
    const q = search.trim().toLowerCase();
    return stockRows.filter((row) => {
      const m = materials[row.material];
      return m && (m.material_name.toLowerCase().includes(q) || m.material_code.toLowerCase().includes(q));
    });
  }, [stockRows, materials, search]);

  const openEdit = (row) => {
    setEditing(row);
    setFormState({
      current_stock: row.current_stock,
      reserved_stock: row.reserved_stock,
      available_stock: row.available_stock,
    });
    setFormError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await client.patch(`/stock/${editing.id}/`, formState);
      setEditing(null);
      await load();
    } catch (err) {
      setFormError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const columns = [
    { key: 'material_name', header: 'Material', render: (row) => materials[row.material]?.material_name || `#${row.material}` },
    { key: 'material_code', header: 'Code', render: (row) => materials[row.material]?.material_code || '-' },
    { key: 'current_stock', header: 'Current Stock' },
    { key: 'reserved_stock', header: 'Reserved' },
    { key: 'available_stock', header: 'Available' },
    { key: 'last_purchase_price', header: 'Last Purchase Price', render: (row) => row.last_purchase_price ?? '-' },
    { key: 'average_purchase_price', header: 'Avg Purchase Price', render: (row) => row.average_purchase_price ?? '-' },
    {
      key: 'low',
      header: 'Alert',
      render: (row) => {
        const min = Number(materials[row.material]?.minimum_stock_level ?? 0);
        return Number(row.current_stock) <= min
          ? <span className="badge badge-cancelled">Low Stock</span>
          : <span className="badge badge-active">OK</span>;
      },
    },
  ];

  if (canWrite) {
    columns.push({
      key: '_actions',
      header: 'Actions',
      render: (row) => <button className="btn btn-secondary btn-sm" onClick={() => openEdit(row)}>Adjust</button>,
    });
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Stock</h1>
      </div>

      <ErrorBanner error={error} />

      <div className="filters-bar">
        <input placeholder="Search by material name or code..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      <DataTable columns={columns} rows={filteredRows} loading={loading} emptyMessage="No stock records found." />

      {editing && (
        <Modal title={`Adjust Stock - ${materials[editing.material]?.material_name || ''}`} onClose={() => setEditing(null)}>
          <form onSubmit={handleSubmit}>
            <ErrorBanner message={formError} />
            <div className="form-grid">
              <div className="form-field">
                <label>Current Stock</label>
                <input
                  type="number" step="0.001" value={formState.current_stock}
                  onChange={(e) => setFormState((p) => ({ ...p, current_stock: e.target.value }))}
                />
              </div>
              <div className="form-field">
                <label>Reserved Stock</label>
                <input
                  type="number" step="0.001" value={formState.reserved_stock}
                  onChange={(e) => setFormState((p) => ({ ...p, reserved_stock: e.target.value }))}
                />
              </div>
              <div className="form-field">
                <label>Available Stock</label>
                <input
                  type="number" step="0.001" value={formState.available_stock}
                  onChange={(e) => setFormState((p) => ({ ...p, available_stock: e.target.value }))}
                />
              </div>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
