import Modal from './Modal';

export default function ConfirmDialog({ title = 'Please confirm', message, confirmLabel = 'Confirm', danger = false, onConfirm, onCancel, busy = false }) {
  return (
    <Modal title={title} onClose={onCancel}>
      <p style={{ margin: 0 }}>{message}</p>
      <div className="modal-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={busy}>Cancel</button>
        <button
          type="button"
          className={danger ? 'btn btn-danger' : 'btn btn-primary'}
          onClick={onConfirm}
          disabled={busy}
        >
          {busy ? 'Please wait...' : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
