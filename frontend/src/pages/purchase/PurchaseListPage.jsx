import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import client from '../../api/client';
import usePaginatedList from '../../hooks/usePaginatedList';
import DataTable from '../../components/DataTable';
import ErrorBanner from '../../components/ErrorBanner';
import StatusBadge from '../../components/StatusBadge';
import Pagination from '../../components/Pagination';

export default function PurchaseListPage() {
  const [suppliers, setSuppliers] = useState({});
  const [statusFilter, setStatusFilter] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const filters = useMemo(() => (statusFilter ? { status: statusFilter } : {}), [statusFilter]);
  const { rows, count, loading, error, page, setPage, totalPages } = usePaginatedList('/purchase/', { search, filters });

  useEffect(() => {
    client.get('/supplier/', { params: { page_size: 200 } })
      .then((resp) => {
        const map = {};
        for (const s of resp.data.results) map[s.id] = s.supplier_name;
        setSuppliers(map);
      })
      .catch(() => setSuppliers({}));
  }, []);

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
        <input placeholder="Search purchase #..." value={searchInput} onChange={(e) => setSearchInput(e.target.value)} />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="DRAFT">Draft</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>

      <DataTable columns={columns} rows={rows} loading={loading} emptyMessage="No purchases found." />
      <Pagination page={page} totalPages={totalPages} count={count} onPageChange={setPage} />
    </div>
  );
}
