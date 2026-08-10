import { useEffect, useState } from 'react';
import client from '../../api/client';
import DataTable from '../../components/DataTable';
import ErrorBanner from '../../components/ErrorBanner';

const ACTIONS = ['CREATE', 'UPDATE', 'DELETE', 'CONFIRM', 'CANCEL', 'ACTIVATE', 'DEACTIVATE', 'ROLE_CHANGE', 'PASSWORD_CHANGE', 'STATUS_CHANGE'];

export default function AuditLogPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modelName, setModelName] = useState('');
  const [action, setAction] = useState('');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (modelName) params.model_name = modelName;
      if (action) params.action = action;
      const resp = await client.get('/audit/', { params });
      setRows(resp.data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [modelName, action]);

  const columns = [
    { key: 'timestamp', header: 'Timestamp', render: (r) => new Date(r.timestamp).toLocaleString() },
    { key: 'actor_username', header: 'Actor', render: (r) => r.actor_username || 'system' },
    { key: 'action', header: 'Action' },
    { key: 'model_name', header: 'Model' },
    { key: 'object_repr', header: 'Object', render: (r) => r.object_repr || `#${r.object_id}` },
    { key: 'metadata', header: 'Details', render: (r) => (r.metadata ? JSON.stringify(r.metadata) : '-') },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Audit Log</h1>
      </div>
      <p style={{ color: 'var(--color-text-muted)', fontSize: 13, marginTop: -8, marginBottom: 14 }}>
        Read-only, append-only security and business action log. Never editable through the API.
      </p>

      <ErrorBanner error={error} />

      <div className="filters-bar">
        <input placeholder="Filter by model name (e.g. Purchase)" value={modelName} onChange={(e) => setModelName(e.target.value)} />
        <select value={action} onChange={(e) => setAction(e.target.value)}>
          <option value="">All actions</option>
          {ACTIONS.map((a) => <option key={a} value={a}>{a.replace(/_/g, ' ')}</option>)}
        </select>
      </div>

      <DataTable columns={columns} rows={rows} loading={loading} emptyMessage="No audit entries found." />
    </div>
  );
}
