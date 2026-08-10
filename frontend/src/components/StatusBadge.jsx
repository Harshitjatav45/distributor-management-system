export default function StatusBadge({ status }) {
  if (!status) return null;
  const cls = String(status).toLowerCase().replace(/\s+/g, '_');
  return <span className={`badge badge-${cls}`}>{status.replace(/_/g, ' ')}</span>;
}
