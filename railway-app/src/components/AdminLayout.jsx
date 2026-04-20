/**
 * AdminLayout - Admin panel layout with sidebar navigation.
 * Provides navigation for admin users to manage the railway system.
 */
import React, { useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/SessionAuthContext';
import NotificationBell from './NotificationBell';

const NAV_ITEMS = [
  { path: '/admin', label: 'Dashboard', icon: 'dashboard', exact: true, access: { module: 'dashboard', action: 'view' } },
  { path: '/admin/users', label: 'Users', icon: 'users', access: { module: 'users', action: 'view' } },
  { path: '/admin/trains', label: 'Trains', icon: 'train', access: { module: 'trains', action: 'view' } },
  { path: '/admin/stations', label: 'Stations', icon: 'map-pin', access: { module: 'stations', action: 'view' } },
  { path: '/admin/train-routes', label: 'Train Routes', icon: 'route', access: { module: 'routes', action: 'view' } },
  { path: '/admin/bookings', label: 'Bookings', icon: 'ticket', access: { module: 'bookings', action: 'view' } },
  { path: '/admin/announcements', label: 'Announcements', icon: 'megaphone', access: { module: 'announcements', action: 'view' } },

  // Admin-only tools
  { path: '/admin/admin-users', label: 'Admin Users', icon: 'shield', adminOnly: true },
  { path: '/admin/employee-invitations', label: 'Employee Invitations', icon: 'mail', adminOnly: true },
  { path: '/admin/rbac', label: 'RBAC', icon: 'lock', adminOnly: true },
  { path: '/admin/fares', label: 'Fares', icon: 'dollar', adminOnly: true },
  { path: '/admin/inventory', label: 'Inventory', icon: 'box', adminOnly: true },
  { path: '/admin/settings', label: 'Settings', icon: 'settings', adminOnly: true },
  { path: '/admin/logs', label: 'Admin Logs', icon: 'list', adminOnly: true },
];

const ICON_MAP = {
  dashboard: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
    </svg>
  ),
  users: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  shield: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  ),
  lock: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  ),
  train: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="3" width="16" height="16" rx="2" />
      <path d="M4 11h16" />
      <path d="M12 3v8" />
      <circle cx="8" cy="15" r="1" />
      <circle cx="16" cy="15" r="1" />
      <path d="M8 19l-2 3" />
      <path d="M16 19l2 3" />
    </svg>
  ),
  'map-pin': (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  ),
  route: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="19" r="3" />
      <path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15" />
      <circle cx="18" cy="5" r="3" />
    </svg>
  ),
  ticket: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z" />
      <path d="M13 5v2" />
      <path d="M13 17v2" />
      <path d="M13 11v2" />
    </svg>
  ),
  dollar: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="1" x2="12" y2="23" />
      <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
    </svg>
  ),
  box: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
      <line x1="12" y1="22.08" x2="12" y2="12" />
    </svg>
  ),
  megaphone: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m3 11 18-5v12L3 14v-3z" />
      <path d="M11.6 16.8a3 3 0 1 1-5.8-1.6" />
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  ),
  list: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="8" y1="6" x2="21" y2="6" />
      <line x1="8" y1="12" x2="21" y2="12" />
      <line x1="8" y1="18" x2="21" y2="18" />
      <line x1="3" y1="6" x2="3.01" y2="6" />
      <line x1="3" y1="12" x2="3.01" y2="12" />
      <line x1="3" y1="18" x2="3.01" y2="18" />
    </svg>
  ),
  mail: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
      <polyline points="22,6 12,13 2,6" />
    </svg>
  ),
  lock: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  ),
  logout: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  ),
  menu: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  ),
  close: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  home: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  ),
};

function Icon({ name, size = 20 }) {
  const icon = ICON_MAP[name];
  if (!icon) return null;
  return (
    <span style={{ width: size, height: size, display: 'inline-flex' }}>
      {icon}
    </span>
  );
}

const styles = {
  container: {
    display: 'flex',
    minHeight: '100vh',
    background: 'var(--bg-base, #0f0f0f)',
  },
  sidebar: {
    width: 260,
    background: 'var(--bg-elevated, #1a1a1a)',
    borderRight: '1px solid var(--border, #2a2a2a)',
    display: 'flex',
    flexDirection: 'column',
    position: 'fixed',
    top: 0,
    left: 0,
    bottom: 0,
    zIndex: 100,
    transition: 'transform 0.3s ease',
  },
  sidebarCollapsed: {
    transform: 'translateX(-100%)',
  },
  sidebarHeader: {
    padding: '20px 16px',
    borderBottom: '1px solid var(--border, #2a2a2a)',
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  logo: {
    fontSize: 20,
    fontWeight: 700,
    color: 'var(--text-primary, #fff)',
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  logoIcon: {
    width: 36,
    height: 36,
    borderRadius: 8,
    background: 'linear-gradient(135deg, var(--accent-blue, #3b82f6), var(--accent-purple, #8b5cf6))',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
  },
  nav: {
    flex: 1,
    overflowY: 'auto',
    padding: '12px 8px',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '12px 14px',
    borderRadius: 8,
    color: 'var(--text-secondary, #9ca3af)',
    textDecoration: 'none',
    fontSize: 14,
    fontWeight: 500,
    transition: 'all 0.2s',
    marginBottom: 4,
    cursor: 'pointer',
    border: 'none',
    background: 'none',
    width: '100%',
    textAlign: 'left',
  },
  navItemActive: {
    background: 'var(--accent-blue, #3b82f6)',
    color: '#fff',
  },
  navItemHover: {
    background: 'var(--bg-inset, #252525)',
  },
  sidebarFooter: {
    padding: '16px',
    borderTop: '1px solid var(--border, #2a2a2a)',
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: '50%',
    background: 'var(--accent-amber, #f59e0b)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
    fontWeight: 600,
    fontSize: 16,
  },
  userName: {
    flex: 1,
    overflow: 'hidden',
  },
  userNameText: {
    fontSize: 14,
    fontWeight: 600,
    color: 'var(--text-primary, #fff)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  userRole: {
    fontSize: 12,
    color: 'var(--text-muted, #6b7280)',
  },
  main: {
    flex: 1,
    marginLeft: 260,
    minHeight: '100vh',
    transition: 'margin-left 0.3s ease',
  },
  mainExpanded: {
    marginLeft: 0,
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 24px',
    background: 'var(--bg-elevated, #1a1a1a)',
    borderBottom: '1px solid var(--border, #2a2a2a)',
    position: 'sticky',
    top: 0,
    zIndex: 50,
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
  },
  menuBtn: {
    display: 'none',
    padding: 8,
    background: 'none',
    border: 'none',
    color: 'var(--text-secondary, #9ca3af)',
    cursor: 'pointer',
    borderRadius: 6,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 600,
    color: 'var(--text-primary, #fff)',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  backToSite: {
    padding: '8px 16px',
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 8,
    color: 'var(--text-secondary, #9ca3af)',
    fontSize: 13,
    textDecoration: 'none',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    transition: 'all 0.2s',
  },
  content: {
    padding: 24,
    maxWidth: 1400,
    margin: '0 auto',
  },
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.5)',
    zIndex: 90,
    display: 'none',
  },
};

// Media query styles for mobile
const mobileStyles = `
  @media (max-width: 768px) {
    .admin-sidebar {
      transform: translateX(-100%);
    }
    .admin-sidebar.open {
      transform: translateX(0);
    }
    .admin-main {
      margin-left: 0 !important;
    }
    .admin-menu-btn {
      display: flex !important;
    }
    .admin-overlay.show {
      display: block !important;
    }
  }
`;

export default function AdminLayout() {
  const { user, logout, isAdmin } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const isActive = (item) => {
    if (item.exact) {
      return location.pathname === item.path;
    }
    return location.pathname.startsWith(item.path);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const closeSidebar = () => setSidebarOpen(false);

  const getInitials = (name) => {
    if (!name) return 'A';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const modulePermissions = user?.permissions?.modules || {};
  const hasModuleAction = (module, action) => {
    const actions = modulePermissions?.[module];
    return Array.isArray(actions) && actions.includes(action);
  };

  const visibleNavItems = NAV_ITEMS.filter((item) => {
    if (isAdmin) return true;
    if (item.adminOnly) return false;
    const access = item.access;
    if (!access) return false;
    return hasModuleAction(access.module, access.action);
  });

  const currentPageTitle = NAV_ITEMS.find(item => isActive(item))?.label || 'Admin Panel';

  return (
    <>
      <style>{mobileStyles}</style>
      <div style={styles.container}>
        {/* Overlay for mobile */}
        <div
          className={`admin-overlay ${sidebarOpen ? 'show' : ''}`}
          style={styles.overlay}
          onClick={closeSidebar}
        />

        {/* Sidebar */}
        <aside
          className={`admin-sidebar ${sidebarOpen ? 'open' : ''}`}
          style={styles.sidebar}
        >
          <div style={styles.sidebarHeader}>
            <div style={styles.logo}>
              <div style={styles.logoIcon}>
                <Icon name="train" size={20} />
              </div>
              <span>Railway Admin</span>
            </div>
          </div>

          <nav style={styles.nav}>
            {visibleNavItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={closeSidebar}
                style={{
                  ...styles.navItem,
                  ...(isActive(item) ? styles.navItemActive : {}),
                }}
                onMouseEnter={(e) => {
                  if (!isActive(item)) {
                    e.currentTarget.style.background = 'var(--bg-inset, #252525)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive(item)) {
                    e.currentTarget.style.background = 'none';
                  }
                }}
              >
                <Icon name={item.icon} size={18} />
                {item.label}
              </Link>
            ))}
          </nav>

          <div style={styles.sidebarFooter}>
            <div style={styles.userInfo}>
              <div style={styles.avatar}>
                {getInitials(user?.fullName || user?.Full_Name)}
              </div>
              <div style={styles.userName}>
                <div style={styles.userNameText}>{user?.fullName || user?.Full_Name || 'Admin'}</div>
                <div style={styles.userRole}>{user?.role || user?.Role || 'Administrator'}</div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              style={styles.navItem}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'var(--bg-inset, #252525)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'none';
              }}
            >
              <Icon name="logout" size={18} />
              Logout
            </button>
          </div>
        </aside>

        {/* Main content */}
        <main className="admin-main" style={styles.main}>
          <header style={styles.header}>
            <div style={styles.headerLeft}>
              <button
                className="admin-menu-btn"
                style={styles.menuBtn}
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                <Icon name={sidebarOpen ? 'close' : 'menu'} size={24} />
              </button>
              <h1 style={styles.headerTitle}>{currentPageTitle}</h1>
            </div>
            <div style={styles.headerRight}>
              <NotificationBell compact />
              <Link
                to="/"
                style={styles.backToSite}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'var(--bg-elevated, #1a1a1a)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'var(--bg-inset, #252525)';
                }}
              >
                <Icon name="home" size={16} />
                Back to Site
              </Link>
            </div>
          </header>

          <div style={styles.content}>
            <Outlet />
          </div>
        </main>
      </div>
    </>
  );
}
