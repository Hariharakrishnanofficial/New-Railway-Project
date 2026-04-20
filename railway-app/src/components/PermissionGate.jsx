import React from 'react';
import { useAuth } from '../context/SessionAuthContext';

/**
 * PermissionGate - A UI gate for Role-Based Access Control
 * 
 * Usage:
 * <PermissionGate module="tickets" action="create">
 *   <button>Buy Ticket</button>
 * </PermissionGate>
 * 
 * @param {string} module - The module to check (e.g., 'users', 'trains', 'tickets')
 * @param {string} action - The action to check ('read', 'create', 'edit', 'delete')
 * @returns {React.ReactNode | null} - The children if the user has permission, or null
 */
const PermissionGate = ({ children, module, action }) => {
  const { user, isAdmin } = useAuth();

  // Admins bypass all specific permission checks.
  if (isAdmin) {
    return <>{children}</>;
  }

  // If there's no user, no permissions.
  if (!user) {
    return null;
  }

  const permissions = user.permissions || {};
  const modulePermissions = permissions.modules || {};

  const hasAccess =
    (Array.isArray(modulePermissions?.[module]) && modulePermissions[module].includes(action)) ||
    (Array.isArray(permissions?.[module]) && permissions[module].includes(action)); // legacy flat map

  if (hasAccess) {
    return <>{children}</>;
  }

  return null;
};

export default PermissionGate;
