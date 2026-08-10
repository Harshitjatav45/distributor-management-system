import { useEffect, useState } from 'react';
import client from '../../api/client';
import DataTable from '../../components/DataTable';
import ErrorBanner from '../../components/ErrorBanner';

const TABS = [
  { key: 'purchase', label: 'Purchase Report', apiPath: '/reports/purchase/' },
  { key: 'sales', label: 'Sales Report', apiPath: '/reports/sales/' },
  { key: 'stock', label: 'Stock Report', apiPath: '/reports/stock/' },
  { key: 'customers', label: 'Customer Report', apiPath: '/reports/customers/' },
  { key: 'suppliers', label: 'Supplier Report', apiPath: '/reports/suppliers/' },
  { key: 'ledger', label: 'Ledger Report', apiPath: '/reports/ledger/' },
];

function buildColumns(rows) {
  if (!rows || rows.length === 0) return [];
  return Object.keys(rows[0]).map((key) => ({ key, header: key.replace(/__/g, ' ').replace(/_/g, ' ') }));
}

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState('purchase');
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const tab = TABS.find((t) => t.key === activeTab);
    setLoading(true);
    setError(null);
    client.get(tab.apiPath)
      .then((resp) => setRows(resp.data.map((row, idx) => ({ ...row, _rowKey: idx }))))
      .catch((err) => setError(err))
      .finally(() => setLoading(false));
  }, [activeTab]);

  const columns = buildColumns(rows).filter((c) => c.key !== '_rowKey');

  return (
    <div className="page">
      <div className="page-header">
        <h1>Reports</h1>
      </div>

      <div className="tabs">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`tab-btn${activeTab === t.key ? ' active' : ''}`}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <ErrorBanner error={error} />

      <DataTable columns={columns} rows={rows} loading={loading} rowKey="_rowKey" emptyMessage="No data available for this report." />
    </div>
  );
}
