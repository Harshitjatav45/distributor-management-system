import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import client from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import DataTable from '../../components/DataTable';
import ErrorBanner, { extractErrorMessage } from '../../components/ErrorBanner';
import LoadingSpinner from '../../components/LoadingSpinner';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';
import StatusBadge from '../../components/StatusBadge';
import { aggregateHeaderTotals, computeLine } from '../../utils/lineCalc';

const emptyItemForm = { material: '', quantity: '', received_quantity: '', rate: '', discount_percentage: '0', gst_percentage: '', batch_number: '', remarks: '' };

export default function PurchaseDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const canConfirmCancel = user?.role === 'Admin' || user?.role === 'Manager';

  const [purchase, setPurchase] = useState(null);
  const [supplier, setSupplier] = useState(null);
  const [materials, setMaterials] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [itemModal, setItemModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [itemForm, setItemForm] = useState(emptyItemForm);
  const [itemError, setItemError] = useState(null);
  const [savingItem, setSavingItem] = useState(false);
  const [deleteItemTarget, setDeleteItemTarget] = useState(null);

  const [confirmAction, setConfirmAction] = useState(null); // 'CONFIRM' | 'CANCEL'
  const [actionBusy, setActionBusy] = useState(false);
  const [actionError, setActionError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const purchaseResp = await client.get(`/purchase/${id}/`);
      setPurchase(purchaseResp.data);
      const [supplierResp, materialResp, itemsResp] = await Promise.all([
        client.get(`/supplier/${purchaseResp.data.supplier}/`),
        client.get('/material/', { params: { page_size: 200 } }),
        // The Purchase detail response does not nest its items
        // (PurchaseSerializer only serializes Purchase's own fields, not
        // the reverse `items` relation), and the items endpoint is
        // paginated, so items are fetched filtered server-side via
        // ?purchase=<id> rather than fetching everything and filtering
        // client-side (which would silently drop items past page 1 of the
        // global list). page_size=200 covers any realistic single
        // purchase's line-item count in one request.
        client.get('/purchase/purchase-items/', { params: { purchase: id, page_size: 200 } }),
      ]);
      setSupplier(supplierResp.data);
      setMaterials(materialResp.data.results);
      setItems(itemsResp.data.results);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const isDraft = purchase?.status === 'DRAFT';
  const materialMap = Object.fromEntries(materials.map((m) => [m.id, m]));

  const recomputeHeader = async (updatedItems) => {
    const totals = aggregateHeaderTotals(updatedItems, purchase.round_off);
    await client.patch(`/purchase/${id}/`, totals);
  };

  const openAddItem = () => {
    setEditingItem(null);
    setItemForm(emptyItemForm);
    setItemError(null);
    setItemModal(true);
  };

  const openEditItem = (item) => {
    setEditingItem(item);
    setItemForm({
      material: item.material,
      quantity: item.quantity,
      received_quantity: item.received_quantity ?? '',
      rate: item.rate,
      discount_percentage: item.discount_percentage,
      gst_percentage: item.gst_percentage,
      batch_number: item.batch_number || '',
      remarks: item.remarks || '',
    });
    setItemError(null);
    setItemModal(true);
  };

  const handleItemSubmit = async (e) => {
    e.preventDefault();
    setSavingItem(true);
    setItemError(null);
    try {
      const material = materialMap[itemForm.material];
      const calc = computeLine(itemForm);
      const payload = {
        purchase: purchase.id,
        material: itemForm.material,
        quantity: itemForm.quantity,
        received_quantity: itemForm.received_quantity === '' ? null : itemForm.received_quantity,
        unit: material?.unit || 'PCS',
        rate: itemForm.rate,
        discount_percentage: itemForm.discount_percentage || 0,
        gst_percentage: itemForm.gst_percentage,
        hsn_code_snapshot: material?.hsn_code || '',
        batch_number: itemForm.batch_number || undefined,
        remarks: itemForm.remarks || undefined,
        ...calc,
      };
      if (!payload.received_quantity) delete payload.received_quantity;
      if (!payload.batch_number) delete payload.batch_number;
      if (!payload.remarks) delete payload.remarks;
      if (!payload.hsn_code_snapshot) delete payload.hsn_code_snapshot;

      let updatedItems;
      if (editingItem) {
        const resp = await client.patch(`/purchase/purchase-items/${editingItem.id}/`, payload);
        updatedItems = items.map((it) => (it.id === editingItem.id ? resp.data : it));
      } else {
        const resp = await client.post('/purchase/purchase-items/', payload);
        updatedItems = [...items, resp.data];
      }
      await recomputeHeader(updatedItems);
      setItemModal(false);
      await load();
    } catch (err) {
      setItemError(extractErrorMessage(err));
    } finally {
      setSavingItem(false);
    }
  };

  const handleDeleteItem = async () => {
    setSavingItem(true);
    try {
      await client.delete(`/purchase/purchase-items/${deleteItemTarget.id}/`);
      const updatedItems = items.filter((it) => it.id !== deleteItemTarget.id);
      await recomputeHeader(updatedItems);
      setDeleteItemTarget(null);
      await load();
    } catch (err) {
      setError(err);
      setDeleteItemTarget(null);
    } finally {
      setSavingItem(false);
    }
  };

  const handleStatusAction = async () => {
    setActionBusy(true);
    setActionError(null);
    try {
      const newStatus = confirmAction === 'CONFIRM' ? 'CONFIRMED' : 'CANCELLED';
      await client.patch(`/purchase/${id}/`, { status: newStatus });
      setConfirmAction(null);
      await load();
    } catch (err) {
      setActionError(extractErrorMessage(err));
    } finally {
      setActionBusy(false);
    }
  };

  if (loading) return <div className="page"><LoadingSpinner /></div>;
  if (error) return <div className="page"><ErrorBanner error={error} /></div>;
  if (!purchase) return null;

  const itemColumns = [
    { key: 'material', header: 'Material', render: (r) => materialMap[r.material]?.material_name || `#${r.material}` },
    { key: 'quantity', header: 'Qty' },
    { key: 'received_quantity', header: 'Received', render: (r) => r.received_quantity ?? '-' },
    { key: 'unit', header: 'Unit' },
    { key: 'rate', header: 'Rate' },
    { key: 'discount_percentage', header: 'Disc %' },
    { key: 'taxable_amount', header: 'Taxable' },
    { key: 'gst_percentage', header: 'GST %' },
    { key: 'gst_amount', header: 'GST Amt' },
    { key: 'line_total', header: 'Line Total' },
  ];
  if (isDraft) {
    itemColumns.push({
      key: '_actions',
      header: 'Actions',
      render: (r) => (
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn btn-secondary btn-sm" onClick={() => openEditItem(r)}>Edit</button>
          <button className="btn btn-danger btn-sm" onClick={() => setDeleteItemTarget(r)}>Delete</button>
        </div>
      ),
    });
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Purchase {purchase.purchase_number} <StatusBadge status={purchase.status} /></h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={() => navigate('/purchases')}>Back</button>
          {isDraft && canConfirmCancel && (
            <button className="btn btn-primary" onClick={() => setConfirmAction('CONFIRM')} disabled={items.length === 0}>Confirm</button>
          )}
          {purchase.status === 'CONFIRMED' && canConfirmCancel && (
            <button className="btn btn-danger" onClick={() => setConfirmAction('CANCEL')}>Cancel Purchase</button>
          )}
          {isDraft && (
            <button className="btn btn-danger" onClick={() => setConfirmAction('CANCEL')}>Void Draft</button>
          )}
        </div>
      </div>

      <ErrorBanner message={actionError} />

      <div className="card" style={{ padding: 16, marginBottom: 18 }}>
        <div className="form-grid">
          <Field label="Supplier" value={supplier?.supplier_name} />
          <Field label="Purchase Date" value={purchase.purchase_date} />
          <Field label="Invoice Number" value={purchase.invoice_number || '-'} />
          <Field label="Payment Status" value={purchase.payment_status} />
          <Field label="Total Amount" value={purchase.total_amount} />
          <Field label="Discount Amount" value={purchase.discount_amount} />
          <Field label="GST Amount" value={purchase.gst_amount} />
          <Field label="Grand Total" value={purchase.grand_total} />
        </div>
      </div>

      <div className="page-header">
        <h2 style={{ fontSize: 15 }}>Items</h2>
        {isDraft && <button className="btn btn-primary btn-sm" onClick={openAddItem}>+ Add Item</button>}
      </div>
      <DataTable columns={itemColumns} rows={items} emptyMessage="No items added yet." />

      {itemModal && (
        <Modal title={editingItem ? 'Edit Item' : 'Add Item'} onClose={() => setItemModal(false)}>
          <form onSubmit={handleItemSubmit}>
            <ErrorBanner message={itemError} />
            <div className="form-grid">
              <div className="form-field">
                <label>Material *</label>
                <select required value={itemForm.material} onChange={(e) => setItemForm((p) => ({ ...p, material: e.target.value }))}>
                  <option value="">-- Select --</option>
                  {materials.map((m) => <option key={m.id} value={m.id}>{m.material_name}</option>)}
                </select>
              </div>
              <div className="form-field">
                <label>Quantity *</label>
                <input type="number" step="0.001" required value={itemForm.quantity} onChange={(e) => setItemForm((p) => ({ ...p, quantity: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Received Quantity</label>
                <input type="number" step="0.001" value={itemForm.received_quantity} onChange={(e) => setItemForm((p) => ({ ...p, received_quantity: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Rate *</label>
                <input type="number" step="0.01" required value={itemForm.rate} onChange={(e) => setItemForm((p) => ({ ...p, rate: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Discount %</label>
                <input type="number" step="0.01" value={itemForm.discount_percentage} onChange={(e) => setItemForm((p) => ({ ...p, discount_percentage: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>GST % *</label>
                <input type="number" step="0.01" required value={itemForm.gst_percentage} onChange={(e) => setItemForm((p) => ({ ...p, gst_percentage: e.target.value }))} />
              </div>
              <div className="form-field">
                <label>Batch Number</label>
                <input value={itemForm.batch_number} onChange={(e) => setItemForm((p) => ({ ...p, batch_number: e.target.value }))} />
              </div>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setItemModal(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={savingItem}>{savingItem ? 'Saving...' : 'Save Item'}</button>
            </div>
          </form>
        </Modal>
      )}

      {deleteItemTarget && (
        <ConfirmDialog
          title="Delete item"
          message="Remove this item from the purchase?"
          confirmLabel="Delete"
          danger
          busy={savingItem}
          onConfirm={handleDeleteItem}
          onCancel={() => setDeleteItemTarget(null)}
        />
      )}

      {confirmAction && (
        <ConfirmDialog
          title={confirmAction === 'CONFIRM' ? 'Confirm Purchase' : 'Cancel Purchase'}
          message={
            confirmAction === 'CONFIRM'
              ? 'This will increase stock and post a Ledger entry for the supplier. Continue?'
              : 'This will reverse stock and post a reversing Ledger entry (if previously confirmed). Continue?'
          }
          confirmLabel={confirmAction === 'CONFIRM' ? 'Confirm' : 'Cancel Purchase'}
          danger={confirmAction === 'CANCEL'}
          busy={actionBusy}
          onConfirm={handleStatusAction}
          onCancel={() => setConfirmAction(null)}
        />
      )}
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div className="form-field">
      <label>{label}</label>
      <div style={{ fontSize: 13, fontWeight: 600 }}>{value ?? '-'}</div>
    </div>
  );
}
