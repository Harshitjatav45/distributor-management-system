import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../../api/client';
import DataTable from '../../components/DataTable';
import ErrorBanner from '../../components/ErrorBanner';
import StatusBadge from '../../components/StatusBadge';

export default function SalesListPage() {
  const [rows, setRows] = useState([]);
  const [customers, setCustomers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [salesResp, customerResp] = await Promise.all([client.get('/sales/'), client.get('/customer/')]);
        setRows(salesResp.data);
        const map = {};
        for (const c of customerResp.data) map[c.id] = c.customer_name;
        setCustomers(map);
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
      .filter((r) => !search.trim() || r.sales_number.toLowerCase().includes(search.trim().toLowerCase()))
      .sort((a, b) => b.id - a.id);
  }, [rows, statusFilter, search]);

  const columns = [
    { key: 'sales_number', header: 'Sales #', render: (r) => <Link to={`/sales/${r.id}`}>{r.sales_number}</Link> },
    { key: 'customer', header: 'Customer', render: (r) => customers[r.customer] || `#${r.customer}` },
    { key: 'sales_date', header: 'Date' },
    { key: 'grand_total', header: 'Grand Total' },
    { key: 'payment_status', header: 'Payment' },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Sales</h1>
        <Link to="/sales/new" className="btn btn-primary">+ New Sales</Link>
      </div>

      <ErrorBanner error={error} />

      <div className="filters-bar">
        <input placeholder="Search sales #..." value={search} onChange={(e) => setSearch(e.target.value)} />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="DRAFT">Draft</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>

      <DataTable columns={columns} rows={filteredRows} loading={loading} emptyMessage="No sales orders found." />
    </div>
  );
}
