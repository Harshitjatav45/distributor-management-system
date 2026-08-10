import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import ProtectedRoute from './auth/ProtectedRoute';
import AppLayout from './layout/AppLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Forbidden from './pages/Forbidden';
import NotFound from './pages/NotFound';
import Companies from './pages/masterdata/Companies';
import Categories from './pages/masterdata/Categories';
import Materials from './pages/masterdata/Materials';
import Suppliers from './pages/masterdata/Suppliers';
import Customers from './pages/masterdata/Customers';
import StockPage from './pages/stock/StockPage';
import PurchaseListPage from './pages/purchase/PurchaseListPage';
import PurchaseCreatePage from './pages/purchase/PurchaseCreatePage';
import PurchaseDetailPage from './pages/purchase/PurchaseDetailPage';
import SalesListPage from './pages/sales/SalesListPage';
import SalesCreatePage from './pages/sales/SalesCreatePage';
import SalesDetailPage from './pages/sales/SalesDetailPage';
import PaymentListPage from './pages/payment/PaymentListPage';
import DispatchListPage from './pages/dispatch/DispatchListPage';
import LedgerPage from './pages/ledger/LedgerPage';
import ReportsPage from './pages/reports/ReportsPage';
import UsersPage from './pages/users/UsersPage';
import AuditLogPage from './pages/audit/AuditLogPage';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/forbidden" element={<Forbidden />} />

          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<Dashboard />} />

            <Route path="/companies" element={<Companies />} />
            <Route path="/categories" element={<Categories />} />
            <Route path="/materials" element={<Materials />} />
            <Route path="/suppliers" element={<Suppliers />} />
            <Route path="/customers" element={<Customers />} />

            <Route path="/stock" element={<StockPage />} />

            <Route path="/purchases" element={<PurchaseListPage />} />
            <Route path="/purchases/new" element={<PurchaseCreatePage />} />
            <Route path="/purchases/:id" element={<PurchaseDetailPage />} />

            <Route path="/sales" element={<SalesListPage />} />
            <Route path="/sales/new" element={<SalesCreatePage />} />
            <Route path="/sales/:id" element={<SalesDetailPage />} />

            <Route path="/dispatch" element={<DispatchListPage />} />

            <Route
              path="/payments"
              element={<ProtectedRoute roles={['Admin', 'Manager']}><PaymentListPage /></ProtectedRoute>}
            />
            <Route
              path="/ledger"
              element={<ProtectedRoute roles={['Admin', 'Manager']}><LedgerPage /></ProtectedRoute>}
            />
            <Route
              path="/reports"
              element={<ProtectedRoute roles={['Admin', 'Manager']}><ReportsPage /></ProtectedRoute>}
            />
            <Route
              path="/users"
              element={<ProtectedRoute roles={['Admin']}><UsersPage /></ProtectedRoute>}
            />
            <Route
              path="/audit-log"
              element={<ProtectedRoute roles={['Admin']}><AuditLogPage /></ProtectedRoute>}
            />
          </Route>

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
