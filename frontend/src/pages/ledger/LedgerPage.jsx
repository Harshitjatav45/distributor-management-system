import { useEffect, useMemo, useState } from 'react';
import client from '../../api/client';
import usePaginatedList from '../../hooks/usePaginatedList';
import DataTable from '../../components/DataTable';
import ErrorBanner from '../../components/ErrorBanner';
import Pagination from '../../components/Pagination';

export default function LedgerPage() {
  const [customers, setCustomers] = useState({});
  const [suppliers, setSuppliers] = useState({});
  const [typeFilter, setTypeFilter] = useState('');

  const filters = useMemo(() => (typeFilter ? { reference_type: typeFilter } : {}), [typeFilter]);
  const { rows, count, loading, error, page, setPage, totalPages } = usePaginatedList('/ledger/', { filters });

  useEffect(() => {
    Promise.all([
      client.get('/customer/', { params: { page_size: 200 } }),
      client.get('/supplier/', { params: { page_size: 200 } }),
    ]).then(([custResp, supResp]) => {
      setCustomers(Object.fromEntries(custResp.data.results.map((c) => [c.id, c.customer_name])));
      setSuppliers(Object.fromEntries(supResp.data.results.map((s) => [s.id, s.supplier_name])));
    }).catch(() => { setCustomers({}); setSuppliers({}); });
  }, []);

  const columns = [
    { key: 'transaction_date', header: 'Date' },
    { key: 'reference_type', header: 'Reference' },
    { key: 'reference_id', header: 'Ref #', render: (r) => r.reference_id ?? '-' },
    { key: 'party', header: 'Party', render: (r) => (r.customer ? customers[r.customer] : suppliers[r.supplier]) || '-' },
    { key: 'entry_type', header: 'Entry' },
    { key: 'amount', header: 'Amount' },
    { key: 'balance', header: 'Balance' },
    { key: 'remarks', header: 'Remarks', render: (r) => r.remarks || '-' },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Ledger</h1>
      </div>
      <p style={{ color: 'var(--color-text-muted)', fontSize: 13, marginTop: -8, marginBottom: 14 }}>
        Read-only financial ledger. Entries are posted automatically by Purchase, Sales, and Payment transactions.
      </p>

      <ErrorBanner error={error} />

      <div className="filters-bar">
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">All references</option>
          <option value="PURCHASE">Purchase</option>
          <option value="SALES">Sales</option>
          <option value="PAYMENT_IN">Payment In</option>
          <option value="PAYMENT_OUT">Payment Out</option>
          <option value="OPENING">Opening</option>
        </select>
      </div>

      <DataTable columns={columns} rows={rows} loading={loading} emptyMessage="No ledger entries found." />
      <Pagination page={page} totalPages={totalPages} count={count} onPageChange={setPage} />
    </div>
  );
}
