export default function Pagination({ page, totalPages, count, onPageChange }) {
  if (count === 0) return null;

  return (
    <div className="pagination-bar">
      <span className="pagination-summary">{count} total record{count === 1 ? '' : 's'}</span>
      <div className="pagination-controls">
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          Previous
        </button>
        <span className="pagination-page-label">Page {page} of {totalPages}</span>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
        >
          Next
        </button>
      </div>
    </div>
  );
}
