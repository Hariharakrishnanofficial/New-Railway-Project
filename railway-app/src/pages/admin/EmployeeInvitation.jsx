import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Input, Badge, Select, PageHeader, StatCard, EmptyState } from "../../components/UI";
import sessionApi from "../../services/sessionApi";

const EmployeeInvitation = () => {
  const [formData, setFormData] = useState({
    email: "",
    role: "Employee",
    department: "",
    designation: "",
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });
  const [invitations, setInvitations] = useState([]);
  const navigate = useNavigate();

  const roleOptions = [
    { value: "Employee", label: "Employee" },
    { value: "Admin", label: "Admin" },
  ];

  useEffect(() => {
    loadInvitations();
  }, []);

  const loadInvitations = async () => {
    try {
      const response = await sessionApi.get("/admin/employees/invitations");
      setInvitations(response.data?.data?.invitations ?? []);
    } catch (error) {
      console.error("Failed to load invitations:", error);
    }
  };

  const stats = useMemo(() => {
    let total = invitations.length;
    let pending = 0;
    let expired = 0;
    let used = 0;

    invitations.forEach((invitation) => {
      if (invitation.used_at) {
        used += 1;
        return;
      }
      const expiresAt = new Date(invitation.expires_at);
      if (expiresAt <= new Date()) {
        expired += 1;
      } else {
        pending += 1;
      }
    });

    return { total, pending, expired, used };
  }, [invitations]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSendInvitation = async (e) => {
    e.preventDefault();

    if (!formData.email.trim()) {
      setMessage({ type: "error", text: "Email is required" });
      return;
    }

    if (!formData.email.includes("@") || !formData.email.includes(".")) {
      setMessage({ type: "error", text: "Please enter a valid email address" });
      return;
    }

    setLoading(true);
    setMessage({ type: "", text: "" });

    try {
      await sessionApi.post("/admin/employees/invite", formData);

      setMessage({
        type: "success",
        text: `Invitation sent successfully to ${formData.email}`,
      });

      setFormData({
        email: "",
        role: "Employee",
        department: "",
        designation: "",
      });
      loadInvitations(); // Refresh list
    } catch (error) {
      const errorMessage =
        error.response?.data?.message ||
        "Failed to send invitation. Please try again.";
      setMessage({ type: "error", text: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshInvitation = async (invitationId) => {
    setLoading(true);
    setMessage({ type: "", text: "" });

    try {
      await sessionApi.post(`/admin/employees/invitations/${invitationId}/refresh`);
      setMessage({ type: "success", text: "Invitation refreshed and resent." });
      loadInvitations();
    } catch (error) {
      const errorMessage =
        error.response?.data?.message ||
        "Failed to refresh invitation. Please try again.";
      setMessage({ type: "error", text: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleReinvite = async (invitationId) => {
    setLoading(true);
    setMessage({ type: "", text: "" });

    try {
      await sessionApi.post(`/admin/employees/invitations/${invitationId}/reinvite`);
      setMessage({
        type: "success",
        text: "New invitation sent successfully.",
      });
      loadInvitations();
    } catch (error) {
      const errorMessage =
        error.response?.data?.message ||
        "Failed to reinvite employee. Please try again.";
      setMessage({ type: "error", text: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (invitation) => {
    if (invitation.used_at) {
      return <Badge status="confirmed" />;
    }

    const expiresAt = new Date(invitation.expires_at);
    const now = new Date();

    if (expiresAt <= now) {
      return <Badge status="cancelled" />;
    }

    return <Badge status="pending" />;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <PageHeader
        icon="users"
        iconAccent="#60a5fa"
        title="Employee Invitations"
        subtitle="Invite new staff members and track acceptance status."
      >
        <Button variant="secondary" onClick={() => navigate("/admin/admin-users")}>Admin Users</Button>
        <Button variant="ghost" onClick={loadInvitations} disabled={loading}>Refresh</Button>
      </PageHeader>

      <div
        style={{
          display: "grid",
          gap: 16,
          gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
        }}
      >
        <StatCard label="Total Invitations" value={stats.total} icon="users" accent="#60a5fa" />
        <StatCard label="Pending" value={stats.pending} icon="clock" accent="#f59e0b" />
        <StatCard label="Expired" value={stats.expired} icon="x" accent="#f87171" />
        <StatCard label="Accepted" value={stats.used} icon="check" accent="#22c55e" />
      </div>

      <Card>
        <div style={{ marginBottom: 18 }}>
          <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>Invite New Employee</h3>
          <p style={{ margin: "6px 0 0", color: "var(--text-muted)", fontSize: 13 }}>
            Invitations expire automatically. Use Refresh or Reinvite to extend access.
          </p>
        </div>
        <form onSubmit={handleSendInvitation} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            <Input
              label="Employee Email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="employee@example.com"
              required
            />
            <Select
              label="Role"
              name="role"
              value={formData.role}
              onChange={handleInputChange}
              required
              options={roleOptions}
            />
          </div>

          <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            <Input
              label="Department (Optional)"
              name="department"
              type="text"
              value={formData.department}
              onChange={handleInputChange}
              placeholder="Operations, Customer Service"
            />
            <Input
              label="Designation (Optional)"
              name="designation"
              type="text"
              value={formData.designation}
              onChange={handleInputChange}
              placeholder="Station Manager"
            />
          </div>

          {message.text && (
            <div
              style={{
                padding: 12,
                borderRadius: "var(--radius-md)",
                background: message.type === "error" ? "#2a0f0f" : "#0f1e2a",
                color: message.type === "error" ? "#f87171" : "#60a5fa",
                border:
                  message.type === "error"
                    ? "1px solid #ef444430"
                    : "1px solid #3b82f630",
                fontSize: 14,
              }}
            >
              {message.text}
            </div>
          )}

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Button type="submit" disabled={loading}>
              {loading ? "Sending Invitation..." : "Send Invitation"}
            </Button>
            <Button type="button" variant="ghost" onClick={() => setFormData({ email: "", role: "Employee", department: "", designation: "" })}>
              Clear
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>Recent Invitations</h3>
          <p style={{ margin: 0, color: "var(--text-muted)", fontSize: 12 }}>
            Showing {invitations.length} invitation{invitations.length === 1 ? "" : "s"}
          </p>
        </div>
        {invitations.length === 0 ? (
          <EmptyState
            icon="info"
            title="No invitations yet"
            description="Send an invitation to onboard your first employee."
          />
        ) : (
          <div style={{ width: "100%", overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", fontSize: 12, textTransform: "uppercase", color: "var(--text-muted)" }}>
                  <th style={{ padding: "12px 10px" }}>Email</th>
                  <th style={{ padding: "12px 10px" }}>Role</th>
                  <th style={{ padding: "12px 10px" }}>Department</th>
                  <th style={{ padding: "12px 10px" }}>Designation</th>
                  <th style={{ padding: "12px 10px" }}>Status</th>
                  <th style={{ padding: "12px 10px" }}>Sent</th>
                  <th style={{ padding: "12px 10px" }}>Expires</th>
                  <th style={{ padding: "12px 10px" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {invitations.map((invitation) => {
                  const expiresAt = new Date(invitation.expires_at);
                  const isExpired = expiresAt <= new Date();
                  const canAct = !invitation.used_at;

                  return (
                    <tr key={invitation.id} style={{ borderTop: "1px solid var(--border)" }}>
                      <td style={{ padding: "14px 10px", fontWeight: 600 }}>{invitation.email}</td>
                      <td style={{ padding: "14px 10px" }}>
                        <span
                          style={{
                            padding: "2px 8px",
                            borderRadius: "4px",
                            fontSize: "12px",
                            fontWeight: 600,
                            background: String(invitation.role || '').toLowerCase() === "admin" ? "#3b82f620" : "#10b98120",
                            color: String(invitation.role || '').toLowerCase() === "admin" ? "#3b82f6" : "#10b981",
                          }}
                        >
                          {invitation.role || "Employee"}
                        </span>
                      </td>
                      <td style={{ padding: "14px 10px", color: "var(--text-muted)" }}>
                        {invitation.department || "-"}
                      </td>
                      <td style={{ padding: "14px 10px", color: "var(--text-muted)" }}>
                        {invitation.designation || "-"}
                      </td>
                      <td style={{ padding: "14px 10px" }}>{getStatusBadge(invitation)}</td>
                      <td style={{ padding: "14px 10px", color: "var(--text-muted)" }}>
                        {formatDate(invitation.invited_at)}
                      </td>
                      <td style={{ padding: "14px 10px", color: "var(--text-muted)" }}>
                        {formatDate(invitation.expires_at)}
                      </td>
                      <td style={{ padding: "14px 10px" }}>
                        {canAct && (
                          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                            {isExpired && (
                              <Button
                                type="button"
                                size="sm"
                                onClick={() => handleRefreshInvitation(invitation.id)}
                                disabled={loading}
                              >
                                Refresh
                              </Button>
                            )}
                            <Button
                              type="button"
                              size="sm"
                              variant={isExpired ? "secondary" : "ghost"}
                              onClick={() => handleReinvite(invitation.id)}
                              disabled={loading}
                            >
                              Reinvite
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};

export default EmployeeInvitation;
