import { Navigate, Route, createBrowserRouter, createRoutesFromElements } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { ProtectedRoute, SessionGate } from './components/SessionGate';
import { LoginPage } from './pages/LoginPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { CustomerDetailPage, CustomersPage } from './pages/CustomersPage';
import { InboxPage } from './pages/InboxPage';

// Exported for MemoryRouter tests; no fake authenticated preview route.
export const routes = createRoutesFromElements(
  <Route element={<SessionGate />}>
    <Route path="/login" element={<LoginPage />} />
    <Route element={<ProtectedRoute />}>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<WorkspacePage title="Tổng quan" />} />
        <Route path="inbox" element={<InboxPage />} />
        <Route path="customers" element={<CustomersPage />} />
        <Route path="customers/:id" element={<CustomerDetailPage />} />
        <Route path="products" element={<WorkspacePage title="Sản phẩm" />} />
        <Route path="orders" element={<WorkspacePage title="Đơn hàng" />} />
        <Route path="orders/:id" element={<WorkspacePage title="Chi tiết đơn hàng" />} />
        <Route path="settings" element={<WorkspacePage title="Cài đặt" />} />
        <Route path="*" element={<WorkspacePage title="Không tìm thấy trang" />} />
      </Route>
    </Route>
  </Route>,
);

export function makeRouter() {
  return createBrowserRouter(routes);
}
