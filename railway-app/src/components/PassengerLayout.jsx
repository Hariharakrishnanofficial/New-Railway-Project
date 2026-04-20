/**
 * PassengerLayout.jsx — Main layout for passenger-facing pages.
 * 
 * Features:
 *   - Responsive sidebar navigation
 *   - Mobile bottom navigation
 *   - User profile dropdown
 */

import React, { useState } from 'react';
import { NavLink, useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/SessionAuthContext';
import { formatEmailForDisplay } from '../utils/emailUtils';
import NotificationBell from './NotificationBell';

// Icons as inline SVG components for simplicity
const Icons = {
  Home: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  ),
  Search: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <path d="M21 21l-4.35-4.35" />
    </svg>
  ),
  Ticket: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z" />
      <path d="M13 5v2" />
      <path d="M13 17v2" />
      <path d="M13 11v2" />
    </svg>
  ),
  FileText: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  ),
  User: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  ),
  Train: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="3" width="16" height="16" rx="2" />
      <path d="M4 11h16" />
      <path d="M12 3v8" />
      <circle cx="8" cy="15" r="1" />
      <circle cx="16" cy="15" r="1" />
      <path d="M8 19l-2 3" />
      <path d="M16 19l2 3" />
    </svg>
  ),
  Menu: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  ),
  X: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  LogOut: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  ),
  ChevronDown: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  ),
};

const navItems = [
  { path: '/', label: 'Home', icon: Icons.Home },
  { path: '/search', label: 'Search Trains', icon: Icons.Search },
  { path: '/my-bookings', label: 'My Bookings', icon: Icons.Ticket },
  { path: '/pnr-status', label: 'PNR Status', icon: Icons.FileText },
  { path: '/profile', label: 'Profile', icon: Icons.User },
];

const styles = {
  layout: {
    display: 'flex',
    minHeight: '100vh',
    background: 'var(--bg-base)',
  },
  
  // Sidebar (desktop)
  sidebar: {
    width: 'var(--sidebar-width)',
    background: 'var(--bg-surface)',
    borderRight: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    position: 'fixed',
    top: 0,
    left: 0,
    bottom: 0,
    zIndex: 100,
    transition: 'transform 0.3s ease',
  },
  sidebarHidden: {
    transform: 'translateX(-100%)',
  },
  
  logo: {
    padding: '24px 20px',
    borderBottom: '1px solid var(--border)',
  },
  logoText: {
    fontSize: 20,
    fontWeight: 800,
    fontFamily: 'var(--font-display)',
    color: 'var(--text-primary)',
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  logoIcon: {
    color: 'var(--accent-blue)',
  },
  
  nav: {
    flex: 1,
    padding: '16px 12px',
    overflowY: 'auto',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '12px 16px',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-secondary)',
    fontSize: 14,
    fontWeight: 500,
    textDecoration: 'none',
    transition: 'all 0.2s',
    marginBottom: 4,
  },
  navItemActive: {
    background: 'rgba(59, 130, 246, 0.15)',
    color: 'var(--accent-blue)',
  },
  navItemHover: {
    background: 'var(--bg-elevated)',
    color: 'var(--text-primary)',
  },
  
  userSection: {
    padding: '16px',
    borderTop: '1px solid var(--border)',
  },
  userCard: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '12px',
    borderRadius: 'var(--radius-md)',
    background: 'var(--bg-elevated)',
    cursor: 'pointer',
    position: 'relative',
  },
  userAvatar: {
    width: 36,
    height: 36,
    borderRadius: 'var(--radius-full)',
    background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 14,
    fontWeight: 700,
    color: 'white',
  },
  userInfo: {
    flex: 1,
    minWidth: 0,
  },
  userName: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--text-primary)',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  userEmail: {
    fontSize: 11,
    color: 'var(--text-muted)',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  
  dropdown: {
    position: 'absolute',
    bottom: '100%',
    left: 0,
    right: 0,
    marginBottom: 8,
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    padding: 8,
    boxShadow: 'var(--shadow-md)',
    zIndex: 200,
  },
  dropdownItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '10px 12px',
    borderRadius: 'var(--radius-sm)',
    fontSize: 13,
    color: 'var(--text-secondary)',
    cursor: 'pointer',
    border: 'none',
    background: 'none',
    width: '100%',
    textAlign: 'left',
    transition: 'all 0.2s',
  },
  dropdownItemDanger: {
    color: 'var(--error)',
  },
  
  // Main content
  main: {
    flex: 1,
    marginLeft: 'var(--sidebar-width)',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },
  
  // Topbar (mobile)
  topbar: {
    display: 'none',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 16px',
    background: 'var(--bg-surface)',
    borderBottom: '1px solid var(--border)',
    position: 'sticky',
    top: 0,
    zIndex: 90,
  },
  menuButton: {
    background: 'none',
    border: 'none',
    color: 'var(--text-primary)',
    padding: 8,
    cursor: 'pointer',
  },
  
  // Content
  content: {
    flex: 1,
    padding: '24px',
  },
  
  // Bottom nav (mobile)
  bottomNav: {
    display: 'none',
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    background: 'var(--bg-surface)',
    borderTop: '1px solid var(--border)',
    padding: '8px 0',
    zIndex: 100,
  },
  bottomNavInner: {
    display: 'flex',
    justifyContent: 'space-around',
    alignItems: 'center',
    maxWidth: 480,
    margin: '0 auto',
  },
  bottomNavItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 4,
    padding: '6px 12px',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-muted)',
    fontSize: 10,
    fontWeight: 500,
    textDecoration: 'none',
    transition: 'all 0.2s',
  },
  bottomNavItemActive: {
    color: 'var(--accent-blue)',
  },
  
  // Overlay
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0, 0, 0, 0.6)',
    zIndex: 99,
  },
};

// Mobile breakpoint styles (inline media query workaround)
const getMobileStyles = (isMobile, sidebarOpen) => {
  if (!isMobile) return {};
  
  return {
    sidebar: {
      ...styles.sidebar,
      ...(sidebarOpen ? {} : styles.sidebarHidden),
    },
    main: {
      ...styles.main,
      marginLeft: 0,
      paddingBottom: 70,
    },
    topbar: {
      ...styles.topbar,
      display: 'flex',
    },
    bottomNav: {
      ...styles.bottomNav,
      display: 'block',
    },
  };
};

export default function PassengerLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  
  // Handle resize
  React.useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (!mobile) setSidebarOpen(false);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  const mobileStyles = getMobileStyles(isMobile, sidebarOpen);
  
  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };
  
  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };
  
  const closeSidebar = () => setSidebarOpen(false);
  
  return (
    <div style={styles.layout}>
      {/* Mobile overlay */}
      {isMobile && sidebarOpen && (
        <div style={styles.overlay} onClick={closeSidebar} />
      )}
      
      {/* Sidebar */}
      <aside style={isMobile ? mobileStyles.sidebar : styles.sidebar}>
        <div style={styles.logo}>
          <span style={styles.logoText}>
            <span style={styles.logoIcon}><Icons.Train /></span>
            RailwayBook
          </span>
        </div>
        
        <nav style={styles.nav}>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={closeSidebar}
              style={({ isActive }) => ({
                ...styles.navItem,
                ...(isActive ? styles.navItemActive : {}),
              })}
            >
              <item.icon />
              {item.label}
            </NavLink>
          ))}
        </nav>
        
        <div style={styles.userSection}>
          <div 
            style={styles.userCard}
            onClick={() => setDropdownOpen(!dropdownOpen)}
          >
            <div style={styles.userAvatar}>
              {getInitials(user?.fullName || user?.Full_Name)}
            </div>
            <div style={styles.userInfo}>
              <div style={styles.userName}>
                {user?.fullName || user?.Full_Name || 'User'}
              </div>
              <div style={styles.userEmail}>
                {formatEmailForDisplay(user?.email || user?.Email || '', 'profile')}
              </div>
            </div>
            <Icons.ChevronDown />
            
            {dropdownOpen && (
              <div style={styles.dropdown}>
                <button
                  style={styles.dropdownItem}
                  onClick={() => { navigate('/profile'); setDropdownOpen(false); closeSidebar(); }}
                >
                  <Icons.User />
                  Profile Settings
                </button>
                <button
                  style={{ ...styles.dropdownItem, ...styles.dropdownItemDanger }}
                  onClick={handleLogout}
                >
                  <Icons.LogOut />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>
      
      {/* Main content */}
      <main style={isMobile ? mobileStyles.main : styles.main}>
        {/* Mobile topbar */}
        <header style={isMobile ? mobileStyles.topbar : styles.topbar}>
          <button style={styles.menuButton} onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? <Icons.X /> : <Icons.Menu />}
          </button>
          <span style={styles.logoText}>
            <span style={styles.logoIcon}><Icons.Train /></span>
            RailwayBook
          </span>
          <NotificationBell compact />
        </header>
        
        <div style={styles.content}>
          <Outlet />
        </div>
        
        {/* Mobile bottom nav */}
        <nav style={isMobile ? mobileStyles.bottomNav : styles.bottomNav}>
          <div style={styles.bottomNavInner}>
            {navItems.slice(0, 4).map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => ({
                  ...styles.bottomNavItem,
                  ...(isActive ? styles.bottomNavItemActive : {}),
                })}
              >
                <item.icon />
                {item.label.split(' ')[0]}
              </NavLink>
            ))}
          </div>
        </nav>
      </main>
    </div>
  );
}
