import { Link } from 'react-router-dom';

export default function Forbidden() {
  return (
    <div className="page">
      <div className="card" style={{ padding: 32, textAlign: 'center' }}>
        <h1>403 &mdash; Access denied</h1>
        <p>Your role doesn't have permission to view this page.</p>
        <Link to="/dashboard" className="btn btn-primary" style={{ marginTop: 12 }}>Back to dashboard</Link>
      </div>
    </div>
  );
}
