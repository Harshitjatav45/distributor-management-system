import { useEffect, useState } from 'react';
import client from '../../api/client';
import DataTable from '../../components/DataTable';
import ErrorBanner, { extractErrorMessage } from '../../components/ErrorBanner';
import Modal from '../../components/Modal';

const emptyCreateForm = { username: '', password: '', first_name: '', last_name: '', email: '', group: 'Staff' };

export default function UsersPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState(emptyCreateForm);
  const [createError, setCreateError] = useState(null);
  const [saving, setSaving] = useState(false);

  const [roleTarget, setRoleTarget] = useState(null);
  const [roleValue, setRoleValue] = useState('');
  const [roleError, setRoleError] = useState(null);

  const [passwordTarget, setPasswordTarget] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [passwordError, setPasswordError] = useState(null);
  const [passwordSaving, setPasswordSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await client.get('/users/');
      setRows(resp.data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setCreateForm(emptyCreateForm);
    setCreateError(null);
    setCreateOpen(true);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    setCreateError(null);
    try {
      await client.post('/users/', createForm);
      setCreateOpen(false);
      await load();
    } catch (err) {
      setCreateError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (user) => {
    try {
      await client.patch(`/users/${user.id}/`, { is_active: !user.is_active });
      await load();
    } catch (err) {
      setError(err);
    }
  };

  const openRoleChange = (user) => {
    setRoleTarget(user);
    setRoleValue(user.role === 'Manager' ? 'Manager' : 'Staff');
    setRoleError(null);
  };

  const handleRoleSubmit = async (e) => {
    e.preventDefault();
    setRoleError(null);
    try {
      await client.patch(`/users/${roleTarget.id}/`, { group: roleValue });
      setRoleTarget(null);
      await load();
    } catch (err) {
      setRoleError(extractErrorMessage(err));
    }
  };

  const openPasswordReset = (user) => {
    setPasswordTarget(user);
    setNewPassword('');
    setPasswordError(null);
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordSaving(true);
    setPasswordError(null);
    try {
      await client.post(`/users/${passwordTarget.id}/set-password/`, { new_password: newPassword });
      setPasswordTarget(null);
    } catch (err) {
      setPasswordError(extractErrorMessage(err));
    } finally {
      setPasswordSaving(false);
    }
  };

  const columns = [
    { key: 'username', header: 'Username' },
    { key: 'name', header: 'Name', render: (r) => `${r.first_name} ${r.last_name}`.trim() || '-' },
    { key: 'email', header: 'Email', render: (r) => r.email || '-' },
    { key: 'role', header: 'Role' },
    { key: 'is_active', header: 'Status', render: (r) => <span className={`badge ${r.is_active ? 'badge-active' : 'badge-inactive'}`}>{r.is_active ? 'Active' : 'Inactive'}</span> },
    {
      key: '_actions',
      header: 'Actions',
      render: (r) => (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => openRoleChange(r)}>Change Role</button>
          <button className="btn btn-secondary btn-sm" onClick={() => toggleActive(r)}>{r.is_active ? 'Deactivate' : 'Activate'}</button>
          <button className="btn btn-secondary btn-sm" onClick={() => openPasswordReset(r)}>Set Password</button>
        </div>
      ),
    },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Users</h1>
        <button className="btn btn-primary" onClick={openCreate}>+ New User</button>
      </div>
      <p style={{ color: 'var(--color-text-muted)', fontSize: 13, marginTop: -8, marginBottom: 14 }}>
        Admin accounts are managed outside this screen. This page can only create/manage Manager and Staff users.
      </p>

      <ErrorBanner error={error} />

      <DataTable columns={columns} rows={rows} loading={loading} emptyMessage="No users found." />

      {createOpen && (
        <Modal title="New User" onClose={() => setCreateOpen(false)}>
          <form onSubmit={handleCreate}>
            <ErrorBanner message={createError} />
            <div className="form-grid">
              <div className="form-field">
                <label>Username *</label>
                <input required value={createForm.username} onChange={(e) => setCreateForm((p) => ({ ...p, username: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Password *</label>
                <input type="password" required value={createForm.password} onChange={(e) => setCreateForm((p) => ({ ...p, password: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>First Name</label>
                <input value={createForm.first_name} onChange={(e) => setCreateForm((p) => ({ ...p, first_name: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Last Name</label>
                <input value={createForm.last_name} onChange={(e) => setCreateForm((p) => ({ ...p, last_name: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Email</label>
                <input type="email" value={createForm.email} onChange={(e) => setCreateForm((p) => ({ ...p, email: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Role *</label>
                <select value={createForm.group} onChange={(e) => setCreateForm((p) => ({ ...p, group: e.target.value }))}>
                  <option value="Staff">Staff</option>
                  <option value="Manager">Manager</option>
                </select>
              </div>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setCreateOpen(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating...' : 'Create User'}</button>
            </div>
          </form>
        </Modal>
      )}

      {roleTarget && (
        <Modal title={`Change Role - ${roleTarget.username}`} onClose={() => setRoleTarget(null)}>
          <form onSubmit={handleRoleSubmit}>
            <ErrorBanner message={roleError} />
            <div className="form-field">
              <label>Role</label>
              <select value={roleValue} onChange={(e) => setRoleValue(e.target.value)}>
                <option value="Staff">Staff</option>
                <option value="Manager">Manager</option>
              </select>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setRoleTarget(null)}>Cancel</button>
              <button type="submit" className="btn btn-primary">Save</button>
            </div>
          </form>
        </Modal>
      )}

      {passwordTarget && (
        <Modal title={`Set Password - ${passwordTarget.username}`} onClose={() => setPasswordTarget(null)}>
          <form onSubmit={handlePasswordSubmit}>
            <ErrorBanner message={passwordError} />
            <div className="form-field">
              <label>New Password</label>
              <input type="password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setPasswordTarget(null)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={passwordSaving}>{passwordSaving ? 'Saving...' : 'Set Password'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
