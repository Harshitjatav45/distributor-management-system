import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../../api/client';
import usePaginatedList from '../../hooks/usePaginatedList';
import DataTable from '../../components/DataTable';
import ErrorBanner from '../../components/ErrorBanner';
import StatusBadge from '../../components/StatusBadge';
import Pagination from '../../components/Pagination';

export default function SalesListPage() {
  const [customers, setCustomers] = useState({});
  const [statusFilter, setStatusFilter] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const filters = useMemo(() => (statusFilter ? { status: statusFilter } : {}), [statusFilter]);
  const { rows, count, loading, error, page, setPage, totalPages } = usePaginatedList('/sales/', { search, filters });

  useEffect(() => {
    client.get('/customer/', { params: { page_size: 200 } })
      .then((resp) => {
        const map = {};
        for (const c of resp.data.results) map[c.id] = c.customer_name;
        setCustomers(map);
      })
      .catch(() => setCustomers({}));
  }, []);

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
        <input placeholder="Search sales #..." value={searchInput} onChange={(e) => setSearchInput(e.target.value)} />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="DRAFT">Draft</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>

      <DataTable columns={columns} rows={rows} loading={loading} emptyMessage="No sales orders found." />
      <Pagination page={page} totalPages={totalPages} count={count} onPageChange={setPage} />
    </div>
  );
}
