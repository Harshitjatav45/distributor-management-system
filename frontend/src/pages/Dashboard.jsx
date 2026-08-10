import { useEffect, useState } from 'react';
import client from '../api/client';
import { useAuth } from '../auth/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBanner from '../components/ErrorBanner';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadStats() {
      setLoading(true);
      setError(null);
      try {
        const [companies, customers, suppliers, materials, stock, purchases, sales, dispatches] = await Promise.all([
          client.get('/company/'),
          client.get('/customer/'),
          client.get('/supplier/'),
          client.get('/material/'),
          client.get('/stock/'),
          client.get('/purchase/'),
          client.get('/sales/'),
          client.get('/dispatch/'),
        ]);

        const isAdminOrManager = user?.role === 'Admin' || user?.role === 'Manager';
        let payments = null;
        if (isAdminOrManager) {
          try {
            const paymentResp = await client.get('/payment/');
            payments = paymentResp.data;
          } catch {
            payments = null;
          }
        }

        if (cancelled) return;

        const purchaseData = purchases.data;
        const salesData = sales.data;
        const dispatchData = dispatches.data;
        const stockData = stock.data;
        const materialData = materials.data;

        const minStockByMaterial = new Map(materialData.map((m) => [m.id, Number(m.minimum_stock_level ?? 0)]));
        const lowStockCount = stockData.filter((s) => {
          const min = minStockByMaterial.get(s.material) ?? 0;
          return Number(s.current_stock) <= min;
        }).length;

        setStats({
          companies: companies.data.length,
          customers: customers.data.length,
          suppliers: suppliers.data.length,
          materials: materialData.length,
          stockRecords: stockData.length,
          lowStockCount,
          purchaseTotal: purchaseData.length,
          purchaseDraft: purchaseData.filter((p) => p.status === 'DRAFT').length,
          purchaseConfirmed: purchaseData.filter((p) => p.status === 'CONFIRMED').length,
          salesTotal: salesData.length,
          salesDraft: salesData.filter((s) => s.status === 'DRAFT').length,
          salesConfirmed: salesData.filter((s) => s.status === 'CONFIRMED').length,
          dispatchTotal: dispatchData.length,
          dispatchActive: dispatchData.filter((d) => !['DELIVERED', 'CANCELLED', 'FAILED'].includes(d.status)).length,
          paymentsTotal: payments ? payments.length : null,
        });
      } catch (err) {
        if (!cancelled) setError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadStats();
    return () => { cancelled = true; };
  }, [user]);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Dashboard</h1>
      </div>

      <ErrorBanner error={error} />

      {loading && <LoadingSpinner label="Loading dashboard..." />}

      {!loading && stats && (
        <>
          <div className="section-title">Master Data</div>
          <div className="stat-grid">
            <StatCard label="Companies" value={stats.companies} />
            <StatCard label="Customers" value={stats.customers} />
            <StatCard label="Suppliers" value={stats.suppliers} />
            <StatCard label="Materials" value={stats.materials} />
          </div>

          <div className="section-title">Purchases</div>
          <div className="stat-grid">
            <StatCard label="Total Purchases" value={stats.purchaseTotal} />
            <StatCard label="Draft" value={stats.purchaseDraft} />
            <StatCard label="Confirmed" value={stats.purchaseConfirmed} />
          </div>

          <div className="section-title">Sales</div>
          <div className="stat-grid">
            <StatCard label="Total Sales" value={stats.salesTotal} />
            <StatCard label="Draft" value={stats.salesDraft} />
            <StatCard label="Confirmed" value={stats.salesConfirmed} />
          </div>

          <div className="section-title">Dispatch &amp; Inventory</div>
          <div className="stat-grid">
            <StatCard label="Stock Records" value={stats.stockRecords} />
            <StatCard label="Low Stock Items" value={stats.lowStockCount} />
            <StatCard label="Total Dispatches" value={stats.dispatchTotal} />
            <StatCard label="Active Dispatches" value={stats.dispatchActive} />
            {stats.paymentsTotal !== null && <StatCard label="Total Payments" value={stats.paymentsTotal} />}
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="card stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}
