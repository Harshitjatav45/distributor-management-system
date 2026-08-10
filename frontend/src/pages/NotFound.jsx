import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="page">
      <div className="card" style={{ padding: 32, textAlign: 'center' }}>
        <h1>404 &mdash; Page not found</h1>
        <Link to="/dashboard" className="btn btn-primary" style={{ marginTop: 12 }}>Back to dashboard</Link>
      </div>
    </div>
  );
}
