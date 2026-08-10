import { useEffect, useMemo, useState } from 'react';
import client from '../../api/client';
import DataTable from '../../components/DataTable';
import ErrorBanner from '../../components/ErrorBanner';

export default function LedgerPage() {
  const [rows, setRows] = useState([]);
  const [customers, setCustomers] = useState({});
  const [suppliers, setSuppliers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [typeFilter, setTypeFilter] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [ledgerResp, custResp, supResp] = await Promise.all([
          client.get('/ledger/'), client.get('/customer/'), client.get('/supplier/'),
        ]);
        setRows(ledgerResp.data);
        setCustomers(Object.fromEntries(custResp.data.map((c) => [c.id, c.customer_name])));
        setSuppliers(Object.fromEntries(supResp.data.map((s) => [s.id, s.supplier_name])));
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filteredRows = useMemo(
    () => rows.filter((r) => !typeFilter || r.reference_type === typeFilter),
    [rows, typeFilter]
  );

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

      <DataTable columns={columns} rows={filteredRows} loading={loading} emptyMessage="No ledger entries found." />
    </div>
  );
}
