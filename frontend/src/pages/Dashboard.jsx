import { useEffect, useState } from 'react';
import client from '../api/client';
import { useAuth } from '../auth/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBanner from '../components/ErrorBanner';

// Cheap way to read just the total count from a paginated endpoint without
// fetching every row - DRF's pagination envelope carries `count` regardless
// of page_size, so a page_size=1 request is enough to get an exact total.
function countOnly(path, params = {}) {
  return client.get(path, { params: { ...params, page_size: 1 } }).then((r) => r.data.count);
}

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
        const isAdminOrManager = user?.role === 'Admin' || user?.role === 'Manager';

        const [
          companiesCount, customersCount, suppliersCount,
          materialResp, stockResp,
          purchaseTotal, purchaseDraft, purchaseConfirmed,
          salesTotal, salesDraft, salesConfirmed,
          dispatchTotal, dispatchDispatched, dispatchOutForDelivery,
        ] = await Promise.all([
          countOnly('/company/'),
          countOnly('/customer/'),
          countOnly('/supplier/'),
          // Full result set needed (not just a count) to join minimum_stock_level
          // against Stock rows below - materials/stock are bounded master-data
          // sets, unlike the transactional counts above which use count-only
          // requests specifically because they grow without bound over time.
          client.get('/material/', { params: { page_size: 200 } }),
          client.get('/stock/', { params: { page_size: 200 } }),
          countOnly('/purchase/'),
          countOnly('/purchase/', { status: 'DRAFT' }),
          countOnly('/purchase/', { status: 'CONFIRMED' }),
          countOnly('/sales/'),
          countOnly('/sales/', { status: 'DRAFT' }),
          countOnly('/sales/', { status: 'CONFIRMED' }),
          countOnly('/dispatch/'),
          countOnly('/dispatch/', { status: 'DISPATCHED' }),
          countOnly('/dispatch/', { status: 'OUT_FOR_DELIVERY' }),
        ]);

        let paymentsTotal = null;
        if (isAdminOrManager) {
          try {
            paymentsTotal = await countOnly('/payment/');
          } catch {
            paymentsTotal = null;
          }
        }

        if (cancelled) return;

        const materialData = materialResp.data.results;
        const stockData = stockResp.data.results;
        const minStockByMaterial = new Map(materialData.map((m) => [m.id, Number(m.minimum_stock_level ?? 0)]));
        const lowStockCount = stockData.filter((s) => {
          const min = minStockByMaterial.get(s.material) ?? 0;
          return Number(s.current_stock) <= min;
        }).length;

        setStats({
          companies: companiesCount,
          customers: customersCount,
          suppliers: suppliersCount,
          materials: materialResp.data.count,
          stockRecords: stockResp.data.count,
          lowStockCount,
          purchaseTotal, purchaseDraft, purchaseConfirmed,
          salesTotal, salesDraft, salesConfirmed,
          dispatchTotal,
          dispatchActive: dispatchDispatched + dispatchOutForDelivery,
          paymentsTotal,
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
