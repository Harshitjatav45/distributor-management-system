import { useEffect, useState } from 'react';
import client from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import usePaginatedList from '../../hooks/usePaginatedList';
import DataTable from '../../components/DataTable';
import ErrorBanner, { extractErrorMessage } from '../../components/ErrorBanner';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';
import Pagination from '../../components/Pagination';

function emptyFormState(fields) {
  const state = {};
  for (const f of fields) {
    state[f.name] = f.type === 'checkbox' ? true : '';
  }
  return state;
}

export default function MasterDataPage({ title, singular, apiPath, fields, listColumns, searchFields = [] }) {
  const { user } = useAuth();
  const isAdmin = user?.role === 'Admin';
  // Plain "strip trailing s" mangles words ending in "-ies" (Categories ->
  // Categorie, Companies -> Companie) - callers for those pages pass an
  // explicit singular form; everything else keeps working unchanged.
  const singularTitle = singular || title.replace(/s$/, '');

  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');

  // Debounce the search box so we don't fire a request on every keystroke.
  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const { rows, count, loading, error: listError, page, setPage, totalPages, reload } = usePaginatedList(apiPath, { search });

  const [modalMode, setModalMode] = useState(null); // 'create' | 'edit'
  const [formState, setFormState] = useState(emptyFormState(fields));
  const [editingRow, setEditingRow] = useState(null);
  const [formError, setFormError] = useState(null);
  const [saving, setSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [optionSets, setOptionSets] = useState({});

  useEffect(() => {
    const fetchFields = fields.filter((f) => f.type === 'select' && f.optionsUrl);
    if (fetchFields.length === 0) return;
    (async () => {
      const next = {};
      for (const f of fetchFields) {
        try {
          const resp = await client.get(f.optionsUrl, { params: { page_size: 200 } });
          next[f.name] = resp.data.results.map((item) => ({ value: item.id, label: f.optionLabel(item) }));
        } catch {
          next[f.name] = [];
        }
      }
      setOptionSets((prev) => ({ ...prev, ...next }));
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      reload();
    } catch (err) {
      setFormError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const [deleteError, setDeleteError] = useState(null);

  const handleDelete = async () => {
    setDeleting(true);
    setDeleteError(null);
    try {
      await client.delete(`${apiPath}${deleteTarget.id}/`);
      setDeleteTarget(null);
      reload();
    } catch (err) {
      setDeleteError(extractErrorMessage(err));
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
        <button className="btn btn-primary" onClick={openCreate}>+ Add {singularTitle}</button>
      </div>

      <ErrorBanner error={listError} />

      {searchFields.length > 0 && (
        <div className="filters-bar">
          <input placeholder="Search..." value={searchInput} onChange={(e) => setSearchInput(e.target.value)} />
        </div>
      )}

      <DataTable columns={columns} rows={rows} loading={loading} emptyMessage={`No ${title.toLowerCase()} found.`} />
      <Pagination page={page} totalPages={totalPages} count={count} onPageChange={setPage} />

      {modalMode && (
        <Modal title={editingRow ? `Edit ${singularTitle}` : `Add ${singularTitle}`} onClose={closeModal} wide>
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
          title={`Delete ${singularTitle}`}
          message={deleteError || `Are you sure you want to delete "${deleteTarget[listColumns[0].key]}"? This cannot be undone.`}
          confirmLabel="Delete"
          danger
          busy={deleting}
          onConfirm={handleDelete}
          onCancel={() => { setDeleteTarget(null); setDeleteError(null); }}
        />
      )}
    </div>
  );
}
