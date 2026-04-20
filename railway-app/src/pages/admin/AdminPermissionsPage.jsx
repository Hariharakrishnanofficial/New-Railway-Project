import React, { useCallback, useEffect, useMemo, useState } from 'react';
import sessionApi from '../../services/sessionApi';
import { useAuth } from '../../context/SessionAuthContext';

const styles = {
  page: { padding: 0, maxWidth: 1100 },
  header: { marginBottom: 20 },
  title: { fontSize: 24, fontWeight: 700, color: 'var(--text-primary, #fff)', margin: 0 },
  subtitle: { fontSize: 13, color: 'var(--text-muted, #6b7280)', marginTop: 8 },
  actions: { display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' },
  btn: {
    padding: '10px 16px',
    borderRadius: 8,
    border: '1px solid var(--border, #2a2a2a)',
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 600,
    background: 'var(--bg-inset, #252525)',
    color: 'var(--text-primary, #fff)',
  },
  btnPrimary: {
    background: 'var(--accent-amber, #f59e0b)',
    color: '#0f0f0f',
    border: 'none',
  },
  btnDisabled: { opacity: 0.6, cursor: 'not-allowed' },
  stateInfo: {
    marginBottom: 14,
    fontSize: 13,
    color: 'var(--text-muted, #6b7280)',
  },
  stateError: {
    padding: '10px 12px',
    borderRadius: 8,
    marginBottom: 14,
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.25)',
    color: '#ef4444',
    fontSize: 13,
  },
  stateSuccess: {
    padding: '10px 12px',
    borderRadius: 8,
    marginBottom: 14,
    background: 'rgba(34, 197, 94, 0.1)',
    border: '1px solid rgba(34, 197, 94, 0.25)',
    color: '#22c55e',
    fontSize: 13,
  },
  roleGrid: { display: 'grid', gridTemplateColumns: '1fr', gap: 14 },
  roleCard: {
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 12,
    padding: 16,
    background: 'var(--bg-elevated, #1a1a1a)',
  },
  roleHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    flexWrap: 'wrap',
    gap: 8,
  },
  roleTitle: { fontSize: 17, fontWeight: 700, color: 'var(--text-primary, #fff)' },
  roleMeta: { fontSize: 12, color: 'var(--text-muted, #6b7280)' },
  moduleGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
    gap: 10,
  },
  moduleItem: {
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 10,
    padding: 10,
    background: 'var(--bg-inset, #252525)',
  },
  moduleLabelRow: { display: 'flex', alignItems: 'center', gap: 8 },
  checkbox: { width: 16, height: 16, cursor: 'pointer' },
  moduleName: { fontWeight: 600, color: 'var(--text-primary, #fff)', fontSize: 13 },
  moduleActions: { marginTop: 6, fontSize: 12, color: 'var(--text-muted, #6b7280)' },
  empty: {
    border: '1px dashed var(--border, #2a2a2a)',
    borderRadius: 12,
    padding: 16,
    color: 'var(--text-muted, #6b7280)',
    fontSize: 13,
  },
};

const uniqueStrings = (items) => [...new Set((items || []).filter((value) => typeof value === 'string' && value.trim()))];

const normalizePermissionObject = (permission) => ({
  modules: Object.entries(permission?.modules || {}).reduce((acc, [moduleName, actions]) => {
    acc[moduleName] = uniqueStrings(actions);
    return acc;
  }, {}),
  admin_access: !!permission?.admin_access,
  can_invite_employees: !!permission?.can_invite_employees,
});

const normalizeCatalogObject = (catalog) =>
  Object.entries(catalog || {}).reduce((acc, [moduleName, actions]) => {
    acc[moduleName] = uniqueStrings(actions);
    return acc;
  }, {});

function buildCatalogFromRoles(roles) {
  const derived = {};
  Object.values(roles || {}).forEach((permission) => {
    Object.entries(permission?.modules || {}).forEach(([moduleName, actions]) => {
      derived[moduleName] = uniqueStrings([...(derived[moduleName] || []), ...(actions || [])]);
    });
  });
  return derived;
}

export default function AdminPermissionsPage() {
  const { isAdmin } = useAuth();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isDirty, setIsDirty] = useState(false);
  const [rolePermissions, setRolePermissions] = useState({});
  const [moduleCatalog, setModuleCatalog] = useState({});
  const [model, setModel] = useState('role_based');

  const moduleNames = useMemo(() => Object.keys(moduleCatalog).sort((a, b) => a.localeCompare(b)), [moduleCatalog]);

  const loadPermissions = useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const res = await sessionApi.get('/admin/rbac/permissions');
      const payload = res?.data?.data || res?.data || {};

      const rolesSource = payload?.roles || {};
      const normalizedRoles = Object.entries(rolesSource).reduce((acc, [roleName, permission]) => {
        acc[roleName] = normalizePermissionObject(permission);
        return acc;
      }, {});

      const explicitCatalog =
        payload?.module_catalog ||
        payload?.moduleCatalog ||
        payload?.modules_catalog ||
        payload?.catalog?.modules ||
        null;

      const normalizedCatalog = normalizeCatalogObject(explicitCatalog || {});
      const derivedCatalog = buildCatalogFromRoles(normalizedRoles);
      const finalCatalog = { ...derivedCatalog, ...normalizedCatalog };

      setRolePermissions(normalizedRoles);
      setModuleCatalog(finalCatalog);
      setModel(payload?.model || 'role_based');
      setIsDirty(false);
    } catch (fetchError) {
      setError(fetchError?.response?.data?.message || 'Failed to load role permissions.');
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => {
    loadPermissions();
  }, [loadPermissions]);

  const toggleModuleForRole = useCallback((roleName, moduleName, enabled) => {
    setRolePermissions((previous) => {
      const currentRole = previous?.[roleName] || normalizePermissionObject({});
      const nextModules = { ...(currentRole.modules || {}) };

      if (enabled) {
        nextModules[moduleName] = [...(moduleCatalog[moduleName] || [])];
      } else {
        delete nextModules[moduleName];
      }

      return {
        ...previous,
        [roleName]: {
          ...currentRole,
          modules: nextModules,
        },
      };
    });
    setIsDirty(true);
    setSuccess('');
    setError('');
  }, [moduleCatalog]);

  const savePermissions = useCallback(async () => {
    if (!isAdmin) return;
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const canonicalRoles = Object.entries(rolePermissions).reduce((acc, [roleName, permission]) => {
        acc[roleName] = normalizePermissionObject(permission);
        return acc;
      }, {});

      await sessionApi.put('/admin/rbac/permissions', {
        model,
        roles: canonicalRoles,
        module_catalog: moduleCatalog,
      });

      setRolePermissions(canonicalRoles);
      setIsDirty(false);
      setSuccess('Role permissions updated successfully.');
    } catch (saveError) {
      setError(saveError?.response?.data?.message || 'Failed to save role permissions.');
    } finally {
      setSaving(false);
    }
  }, [isAdmin, model, moduleCatalog, rolePermissions]);

  if (!isAdmin) {
    return (
      <div style={styles.page}>
        <h2 style={styles.title}>Role Permissions</h2>
        <div style={styles.stateInfo}>Admin access required.</div>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h2 style={styles.title}>Role Permissions</h2>
        <div style={styles.subtitle}>
          Configure module-level access per role. Enabling a module grants all actions listed in the module catalog.
        </div>
      </div>

      <div style={styles.actions}>
        <button
          type="button"
          style={styles.btn}
          onClick={loadPermissions}
          disabled={loading || saving}
        >
          {loading ? 'Loading...' : 'Reload'}
        </button>
        <button
          type="button"
          style={{ ...styles.btn, ...styles.btnPrimary, ...(saving || !isDirty ? styles.btnDisabled : {}) }}
          onClick={savePermissions}
          disabled={saving || !isDirty}
        >
          {saving ? 'Saving...' : 'Save Permissions'}
        </button>
      </div>

      {error ? <div style={styles.stateError}>{error}</div> : null}
      {success ? <div style={styles.stateSuccess}>{success}</div> : null}
      {!error && !success && (
        <div style={styles.stateInfo}>
          {isDirty ? 'You have unsaved changes.' : 'No pending changes.'}
        </div>
      )}

      {loading ? (
        <div style={styles.stateInfo}>Loading role permissions...</div>
      ) : Object.keys(rolePermissions).length === 0 ? (
        <div style={styles.empty}>No roles found in RBAC response.</div>
      ) : moduleNames.length === 0 ? (
        <div style={styles.empty}>No modules found in RBAC catalog.</div>
      ) : (
        <div style={styles.roleGrid}>
          {Object.entries(rolePermissions).map(([roleName, permission]) => (
            <div key={roleName} style={styles.roleCard}>
              <div style={styles.roleHeader}>
                <div style={styles.roleTitle}>{roleName}</div>
                <div style={styles.roleMeta}>
                  admin_access: {permission.admin_access ? 'true' : 'false'} | can_invite_employees:{' '}
                  {permission.can_invite_employees ? 'true' : 'false'}
                </div>
              </div>

              <div style={styles.moduleGrid}>
                {moduleNames.map((moduleName) => {
                  const enabled = Array.isArray(permission?.modules?.[moduleName]);
                  const moduleActions = moduleCatalog[moduleName] || [];
                  return (
                    <label key={`${roleName}-${moduleName}`} style={styles.moduleItem}>
                      <div style={styles.moduleLabelRow}>
                        <input
                          type="checkbox"
                          style={styles.checkbox}
                          checked={enabled}
                          onChange={(event) =>
                            toggleModuleForRole(roleName, moduleName, event.target.checked)
                          }
                        />
                        <span style={styles.moduleName}>{moduleName}</span>
                      </div>
                      <div style={styles.moduleActions}>
                        Actions: {moduleActions.length ? moduleActions.join(', ') : '-'}
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
