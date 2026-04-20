import { HashRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
// Session-based authentication (HttpOnly cookies, CSRF protection)
// To revert to JWT: change SessionAuthProvider -> AuthProvider, useSessionAuth -> useAuth
import { SessionAuthProvider as AuthProvider, useSessionAuth as useAuth } from './context/SessionAuthContext';
import { ToastProvider } from './context/ToastContext';
import AuthPage from './pages/auth/AuthPage';
import RegisterPage from './pages/auth/RegisterPage';
import PassengerLayout from './components/PassengerLayout';
import AdminLayout from './components/AdminLayout';
import SearchPage from './pages/SearchPage';
import BookingPage from './pages/BookingPage';
import MyBookingsPage from './pages/MyBookingsPage';
import PnrStatusPage from './pages/PnrStatusPage';
import ProfilePage from './pages/ProfilePage';
import CancelTicketPage from './pages/CancelTicketPage';
import NotificationsPage from './pages/NotificationsPage';
// Admin pages
import { DashboardPage, UsersPage, AdminUsersPage, TrainsPage, StationsPage, BookingsPage as AdminBookingsPage, TrainRoutesPage, FaresPage, InventoryPage, AnnouncementsPage, AdminLogsPage, AdminPermissionsPage, SettingsPage, } from './pages/admin'; 
import EmployeeInvitation from './pages/admin/EmployeeInvitation';
import { NotificationProvider } from './context/NotificationContext';
import './styles/global.css';

// Loading Spinner Component
function LoadingSpinner({ color = 'var(--accent-blue)' }) {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-base)',
    }}>
      <div style={{
        width: 40, height: 40, borderRadius: '50%',
        border: '3px solid var(--border)',
        borderTopColor: color,
        animation: 'spin 0.8s linear infinite',
      }} />
    </div>
  );
}

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    // Save the attempted URL for redirect after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

function PassengerRoute({ children }) {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if user is admin or employee - redirect them to admin dashboard
  const role = (user?.role || user?.Role || '').toUpperCase();
  const userType = (user?.type || '').toLowerCase();
  const isEmployee = userType === 'employee';

  if (isEmployee) {
    // Employees/Admins should use admin panel, not passenger pages
    return <Navigate to="/admin" replace />;
  }

  return children;
}

function AdminRoute({ children }) {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner color="var(--accent-amber)" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if user is admin or employee (both can access admin panel)
  const role = (user?.role || user?.Role || '').toUpperCase();
  const userType = (user?.type || '').toLowerCase();
  const isEmployee = userType === 'employee';

  if (!isEmployee) {
    // Passengers should not access admin panel
    return <Navigate to="/" replace />;
  }

  return children;
}

function AdminOnlyRoute({ children }) {
  const { isAdmin, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner color="var(--accent-amber)" />;
  }

  if (!isAdmin) {
    return <Navigate to="/admin" replace />;
  }

  return children;
}

function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (isAuthenticated) {
    // Redirect to the page they were trying to access, or home
    const from = location.state?.from?.pathname || '/';
    return <Navigate to={from} replace />;
  }

  return children;
}

function HomePage() {
  const { user, logout } = useAuth();

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-base)',
      padding: 32,
    }}>
      <div style={{
        maxWidth: 800,
        margin: '0 auto',
      }}>
        <div style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-xl)',
          padding: 32,
        }}>
          <h1 style={{
            fontSize: 28,
            fontWeight: 800,
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-display)',
            margin: '0 0 8px',
          }}>
            Welcome, {user?.fullName}!
          </h1>
          <p style={{ color: 'var(--text-muted)', margin: '0 0 24px' }}>
            You are logged in as {user?.email} ({user?.role})
          </p>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 16,
            marginBottom: 24,
          }}>
            <div style={{
              background: 'var(--bg-inset)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-lg)',
              padding: 20,
            }}>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>Account Status</p>
              <p style={{
                fontSize: 16, fontWeight: 600,
                color: user?.accountStatus === 'Active' ? 'var(--success)' : 'var(--error)',
                margin: '4px 0 0',
              }}>
                {user?.accountStatus || 'Active'}
              </p>
            </div>
            <div style={{
              background: 'var(--bg-inset)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-lg)',
              padding: 20,
            }}>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>Phone Number</p>
              <p style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 0' }}>
                {user?.phoneNumber || 'Not provided'}
              </p>
            </div>
          </div>

          <button
            onClick={logout}
            style={{
              background: '#2a0f0f',
              color: '#f87171',
              border: '1px solid #ef444430',
              borderRadius: 'var(--radius-md)',
              padding: '12px 24px',
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'var(--font-body)',
            }}
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <AuthPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <AuthPage />
          </PublicRoute>
        }
      />
      <Route
        path="/employee-register"
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        }
      />
      <Route
        path="/admin-setup"
        element={
          <PublicRoute>
            <AuthPage />
          </PublicRoute>
        }
      />
      <Route
        path="/forgot-password"
        element={
          <PublicRoute>
            <AuthPage />
          </PublicRoute>
        }
      />
      {/* Passenger Routes with Layout - Only for passengers, not employees/admins */}
      <Route
        path="/"
        element={
          <PassengerRoute>
            <PassengerLayout />
          </PassengerRoute>
        }
      >
        <Route index element={<HomePage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="book" element={<BookingPage />} />
        <Route path="my-bookings" element={<MyBookingsPage />} />
        <Route path="pnr-status" element={<PnrStatusPage />} />
        <Route path="cancel-ticket" element={<CancelTicketPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="notifications" element={<NotificationsPage />} />
      </Route>

      {/* Admin Routes with Admin Layout */}
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <AdminLayout />
          </AdminRoute>
        }
      > 
        <Route index element={<DashboardPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route
          path="admin-users"
          element={
            <AdminOnlyRoute>
              <AdminUsersPage />
            </AdminOnlyRoute>
          }
        />
        <Route path="trains" element={<TrainsPage />} />
        <Route path="stations" element={<StationsPage />} />
        <Route path="bookings" element={<AdminBookingsPage />} />
        <Route path="train-routes" element={<TrainRoutesPage />} />
        <Route
          path="fares"
          element={
            <AdminOnlyRoute>
              <FaresPage />
            </AdminOnlyRoute>
          }
        />
        <Route
          path="inventory"
          element={
            <AdminOnlyRoute>
              <InventoryPage />
            </AdminOnlyRoute>
          }
        />
        <Route path="announcements" element={<AnnouncementsPage />} />
        <Route
          path="employee-invitations"
          element={
            <AdminOnlyRoute>
              <EmployeeInvitation />
            </AdminOnlyRoute>
          }
        />
        <Route
          path="settings"
          element={
            <AdminOnlyRoute>
              <SettingsPage />
            </AdminOnlyRoute>
          }
        />
        <Route
          path="logs"
          element={
            <AdminOnlyRoute>
              <AdminLogsPage />
            </AdminOnlyRoute>
          }
        />
        <Route
          path="rbac"
          element={
            <AdminOnlyRoute>
              <AdminPermissionsPage />
            </AdminOnlyRoute>
          }
        />
        <Route path="permissions" element={<Navigate to="/admin/rbac" replace />} />
        <Route path="notifications" element={<NotificationsPage />} />
      </Route>

      {/* 404 Not Found */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

// 404 Not Found Page
function NotFoundPage() {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-base)',
      padding: 24,
    }}>
      <div style={{
        textAlign: 'center',
        maxWidth: 400,
      }}>
        <h1 style={{ 
          fontSize: 72, 
          fontWeight: 800, 
          color: 'var(--text-primary)', 
          margin: 0,
          fontFamily: 'var(--font-display)',
        }}>
          404
        </h1>
        <p style={{ 
          fontSize: 18, 
          color: 'var(--text-muted)', 
          margin: '16px 0 24px' 
        }}>
          Page not found
        </p>
        <a 
          href="#/" 
          style={{
            display: 'inline-block',
            background: 'var(--accent-blue)',
            color: 'white',
            padding: '12px 24px',
            borderRadius: 'var(--radius-md)',
            textDecoration: 'none',
            fontWeight: 600,
          }}
        >
          Go Home
        </a>
      </div>
    </div>
  );
}

function App() {
  // HashRouter uses URL hash (#) for routing - works reliably with static hosting
  // URLs will be like: /app/#/login, /app/#/search, etc.
  return (
    <HashRouter>
      <ToastProvider>
        <AuthProvider>
          <NotificationProvider>
            <AppRoutes />
          </NotificationProvider>
        </AuthProvider>
      </ToastProvider>
    </HashRouter>
  );
}

export default App;
