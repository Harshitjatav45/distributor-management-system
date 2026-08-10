import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../../api/client';
import DataTable from '../../components/DataTable';
import ErrorBanner from '../../components/ErrorBanner';
import StatusBadge from '../../components/StatusBadge';

export default function PurchaseListPage() {
  const [rows, setRows] = useState([]);
  const [suppliers, setSuppliers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [purchaseResp, supplierResp] = await Promise.all([client.get('/purchase/'), client.get('/supplier/')]);
        setRows(purchaseResp.data);
        const map = {};
        for (const s of supplierResp.data) map[s.id] = s.supplier_name;
        setSuppliers(map);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filteredRows = useMemo(() => {
    return rows
      .filter((r) => !statusFilter || r.status === statusFilter)
      .filter((r) => !search.trim() || r.purchase_number.toLowerCase().includes(search.trim().toLowerCase()))
      .sort((a, b) => b.id - a.id);
  }, [rows, statusFilter, search]);

  const columns = [
    { key: 'purchase_number', header: 'Purchase #', render: (r) => <Link to={`/purchases/${r.id}`}>{r.purchase_number}</Link> },
    { key: 'supplier', header: 'Supplier', render: (r) => suppliers[r.supplier] || `#${r.supplier}` },
    { key: 'purchase_date', header: 'Date' },
    { key: 'grand_total', header: 'Grand Total' },
    { key: 'payment_status', header: 'Payment' },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Purchases</h1>
        <Link to="/purchases/new" className="btn btn-primary">+ New Purchase</Link>
      </div>

      <ErrorBanner error={error} />

      <div className="filters-bar">
        <input placeholder="Search purchase #..." value={search} onChange={(e) => setSearch(e.target.value)} />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="DRAFT">Draft</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>

      <DataTable columns={columns} rows={filteredRows} loading={loading} emptyMessage="No purchases found." />
    </div>
  );
}
