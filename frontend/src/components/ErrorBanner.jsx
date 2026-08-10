export function extractErrorMessage(error) {
  if (!error) return null;
  const data = error.response?.data;
  if (!data) return error.message || 'Something went wrong. Please try again.';
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  const parts = [];
  for (const [key, value] of Object.entries(data)) {
    const text = Array.isArray(value) ? value.join(' ') : String(value);
    parts.push(key === 'non_field_errors' || key === 'status' ? text : `${key}: ${text}`);
  }
  return parts.length ? parts.join(' | ') : 'Something went wrong. Please try again.';
}

export default function ErrorBanner({ error, message }) {
  const text = message || extractErrorMessage(error);
  if (!text) return null;
  return <div className="alert alert-error">{text}</div>;
}
