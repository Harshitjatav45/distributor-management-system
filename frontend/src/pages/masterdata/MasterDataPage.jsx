import { useEffect, useMemo, useState } from 'react';
import client from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import DataTable from '../../components/DataTable';
import ErrorBanner, { extractErrorMessage } from '../../components/ErrorBanner';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';

function emptyFormState(fields) {
  const state = {};
  for (const f of fields) {
    state[f.name] = f.type === 'checkbox' ? true : '';
  }
  return state;
}

export default function MasterDataPage({ title, apiPath, fields, listColumns, searchFields = [] }) {
  const { user } = useAuth();
  const isAdmin = user?.role === 'Admin';

  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');

  const [modalMode, setModalMode] = useState(null); // 'create' | 'edit'
  const [formState, setFormState] = useState(emptyFormState(fields));
  const [editingRow, setEditingRow] = useState(null);
  const [formError, setFormError] = useState(null);
  const [saving, setSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [optionSets, setOptionSets] = useState({});

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await client.get(apiPath);
      setRows(resp.data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiPath]);

  useEffect(() => {
    const fetchFields = fields.filter((f) => f.type === 'select' && f.optionsUrl);
    if (fetchFields.length === 0) return;
    (async () => {
      const next = {};
      for (const f of fetchFields) {
        try {
          const resp = await client.get(f.optionsUrl);
          next[f.name] = resp.data.map((item) => ({ value: item.id, label: f.optionLabel(item) }));
        } catch {
          next[f.name] = [];
        }
      }
      setOptionSets((prev) => ({ ...prev, ...next }));
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredRows = useMemo(() => {
    if (!search.trim() || searchFields.length === 0) return rows;
    const q = search.trim().toLowerCase();
    return rows.filter((row) => searchFields.some((f) => String(row[f] ?? '').toLowerCase().includes(q)));
  }, [rows, search, searchFields]);

  const openCreate = () => {
    setEditingRow(null);
    setFormState(emptyFormState(fields));
    setFormError(null);
    setModalMode('create');
  };

  const openEdit = (row) => {
    setEditingRow(row);
    const state = {};
    for (const f of fields) {
      state[f.name] = row[f.name] ?? (f.type === 'checkbox' ? false : '');
    }
    setFormState(state);
    setFormError(null);
    setModalMode('edit');
  };

  const closeModal = () => {
    setModalMode(null);
    setEditingRow(null);
  };

  const handleFieldChange = (name, value) => {
    setFormState((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const payload = {};
      for (const f of fields) {
        const value = formState[f.name];
        // Omit empty optional fields entirely rather than sending null -
        // several optional fields are blank=True but NOT null=True at the
        // model level, so an explicit null violates the NOT NULL
        // constraint where a model-level default should apply instead.
        if ((f.type === 'number' || f.type === 'select') && value === '' && !f.required) {
          continue;
        }
        payload[f.name] = value;
      }
      if (editingRow) {
        await client.patch(`${apiPath}${editingRow.id}/`, payload);
      } else {
        await client.post(apiPath, payload);
      }
      closeModal();
      await load();
    } catch (err) {
      setFormError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await client.delete(`${apiPath}${deleteTarget.id}/`);
      setDeleteTarget(null);
      await load();
    } catch (err) {
      setError(err);
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  const columns = [
    ...listColumns,
    {
      key: 'is_active',
      header: 'Status',
      render: (row) => (
        <span className={`badge ${row.is_active ? 'badge-active' : 'badge-inactive'}`}>
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      key: '_actions',
      header: 'Actions',
      render: (row) => (
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn btn-secondary btn-sm" onClick={() => openEdit(row)}>Edit</button>
          {isAdmin && (
            <button className="btn btn-danger btn-sm" onClick={() => setDeleteTarget(row)}>Delete</button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>{title}</h1>
        <button className="btn btn-primary" onClick={openCreate}>+ Add {title.replace(/s$/, '')}</button>
      </div>

      <ErrorBanner error={error} />

      {searchFields.length > 0 && (
        <div className="filters-bar">
          <input placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      )}

      <DataTable columns={columns} rows={filteredRows} loading={loading} emptyMessage={`No ${title.toLowerCase()} found.`} />

      {modalMode && (
        <Modal title={editingRow ? `Edit ${title.replace(/s$/, '')}` : `Add ${title.replace(/s$/, '')}`} onClose={closeModal} wide>
          <form onSubmit={handleSubmit}>
            <ErrorBanner message={formError} />
            <div className="form-grid">
              {fields.map((f) => (
                <div className="form-field" key={f.name}>
                  <label htmlFor={f.name}>{f.label}{f.required && ' *'}</label>
                  {f.type === 'select' ? (
                    <select
                      id={f.name}
                      value={formState[f.name] ?? ''}
                      required={f.required}
                      onChange={(e) => handleFieldChange(f.name, e.target.value)}
                    >
                      <option value="">-- Select --</option>
                      {(f.optionsUrl ? optionSets[f.name] : f.choices)?.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  ) : f.type === 'textarea' ? (
                    <textarea
                      id={f.name}
                      value={formState[f.name] ?? ''}
                      required={f.required}
                      rows={3}
                      onChange={(e) => handleFieldChange(f.name, e.target.value)}
                    />
                  ) : f.type === 'checkbox' ? (
                    <input
                      id={f.name}
                      type="checkbox"
                      checked={!!formState[f.name]}
                      style={{ width: 'auto' }}
                      onChange={(e) => handleFieldChange(f.name, e.target.checked)}
                    />
                  ) : (
                    <input
                      id={f.name}
                      type={f.type === 'number' ? 'number' : f.type === 'email' ? 'email' : 'text'}
                      step={f.step}
                      value={formState[f.name] ?? ''}
                      required={f.required}
                      onChange={(e) => handleFieldChange(f.name, e.target.value)}
                    />
                  )}
                </div>
              ))}
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={closeModal}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {deleteTarget && (
        <ConfirmDialog
          title={`Delete ${title.replace(/s$/, '')}`}
          message={`Are you sure you want to delete "${deleteTarget[listColumns[0].key]}"? This cannot be undone.`}
          confirmLabel="Delete"
          danger
          busy={deleting}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
