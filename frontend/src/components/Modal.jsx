export default function Modal({ title, onClose, children, wide = false }) {
  return (
    <div className="modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className={`modal-box${wide ? ' modal-wide' : ''}`}>
        <div className="page-header">
          <h2 style={{ margin: 0, fontSize: 16 }}>{title}</h2>
          <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>Close</button>
        </div>
        {children}
      </div>
    </div>
  );
}
