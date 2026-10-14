import { useState, useEffect, useCallback } from "react";
import api from "../services/api";
import toast from "react-hot-toast";

const REMINDER_TYPES = [
  { value: "PHONE_CALL", label: "Phone Call" },
  { value: "INTERVIEW", label: "Interview" },
  { value: "FOLLOW_UP", label: "Follow Up" },
  { value: "CUSTOM", label: "Custom" },
];

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "PENDING", label: "Pending" },
  { value: "SENT", label: "Sent" },
  { value: "FAILED", label: "Failed" },
  { value: "DISMISSED", label: "Dismissed" },
];

function ReminderModal({ app, onClose, onSuccess }) {
  const [message, setMessage] = useState("");
  const [reminderType, setReminderType] = useState("FOLLOW_UP");
  const [scheduledAt, setScheduledAt] = useState("");
  const [leadTime, setLeadTime] = useState(0);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!scheduledAt) {
      toast.error("Scheduled date/time is required");
      return;
    }
    setSaving(true);
    try {
      await api.post("/api/hr/reminders", {
        application_id: app.id,
        reminder_type: reminderType,
        message,
        scheduled_at: scheduledAt,
        lead_time_minutes: leadTime,
      }, { skipErrorHandler: true });
      toast.success("Reminder created and candidate notified!");
      onSuccess();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to create reminder");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: "500px" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="modal-title">Create Follow-up Reminder</div>
            <div style={{ fontSize: "13px", color: "#777", marginTop: "2px" }}>
              {app.company} — {app.role}
            </div>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#777", fontSize: "20px", cursor: "pointer" }}>✕</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ background: "#0B0B0B", borderRadius: "8px", padding: "12px 14px" }}>
              <div style={{ fontWeight: 600, color: "#fff" }}>{app.candidate?.name}</div>
              <div style={{ fontSize: "12px", color: "#B8B8B8" }}>{app.candidate?.email}</div>
              {app.candidate?.phone_number && (
                <div style={{ fontSize: "12px", color: "#B8B8B8" }}>{app.candidate.phone_number}</div>
              )}
            </div>

            <div>
              <label className="label-gold">Reminder Type</label>
              <select className="input-gold" value={reminderType} onChange={(e) => setReminderType(e.target.value)}>
                {REMINDER_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label-gold">Scheduled At</label>
              <input
                type="datetime-local"
                className="input-gold"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="label-gold">Send Reminder (minutes before)</label>
              <select className="input-gold" value={leadTime} onChange={(e) => setLeadTime(parseInt(e.target.value))}>
                <option value={0}>At scheduled time</option>
                <option value={30}>30 minutes before</option>
                <option value={60}>1 hour before</option>
                <option value={1440}>1 day before</option>
              </select>
            </div>

            <div>
              <label className="label-gold">Message (Optional)</label>
              <textarea
                className="input-gold" rows={3}
                placeholder="Custom reminder message..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                style={{ resize: "vertical" }}
                maxLength={500}
              />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn-outline-gold" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-gold" disabled={saving}>
              {saving ? "Creating..." : "Create Reminder"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function HRReminders() {
  const [reminders, setReminders] = useState([]);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedApp, setSelectedApp] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchReminders = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      const res = await api.get(`/api/hr/reminders?${params}`, { skipErrorHandler: true });
      setReminders(res.data.reminders || []);
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to load reminders");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  const fetchApplications = useCallback(async () => {
    try {
      const res = await api.get("/api/hr/applications?per_page=200", { skipErrorHandler: true });
      setApplications(res.data.applications || []);
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to load applications");
    }
  }, []);

  useEffect(() => {
    document.title = "HR Reminders — Job Tracker";
    fetchReminders();
  }, [fetchReminders]);

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);

  const handleDismiss = async (id) => {
    try {
      await api.patch(`/api/hr/reminders/${id}`, { dismissed: true }, { skipErrorHandler: true });
      toast.success("Reminder dismissed");
      fetchReminders();
     } catch {
      toast.error("Failed to update reminder");
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/api/hr/reminders/${id}`, { skipErrorHandler: true });
      toast.success("Reminder deleted");
      fetchReminders();
    } catch {
      toast.error("Failed to delete reminder");
    }
  };

  const handleCreateReminder = (app) => {
    setSelectedApp(app);
    setModalOpen(true);
  };

  const upcomingReminders = reminders.filter(r => r.status === "PENDING" && !r.sent_at);
  const pastReminders = reminders.filter(r => r.status === "SENT" || r.status === "FAILED" || r.dismissed);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#fff", marginBottom: "6px" }}>
            Follow-up Reminders 🔔
          </h1>
          <p style={{ color: "#777", fontSize: "14px" }}>
            Manage reminders for candidate follow-ups and interview notifications.
          </p>
        </div>
      </div>

      {/* Filters */}
      <div style={{
        background: "#111111", border: "1px solid #1F1F1F",
        borderRadius: "12px", padding: "16px 20px",
        display: "flex", gap: "14px", flexWrap: "wrap", alignItems: "flex-end"
      }}>
        <div style={{ flex: "1 1 160px", minWidth: "140px" }}>
          <label className="label-gold">Status Filter</label>
          <select
            className="input-gold"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
        {(statusFilter || reminders.length > 0) && (
          <button
            className="btn-outline-gold"
            style={{ padding: "8px 14px", fontSize: "13px", alignSelf: "flex-end" }}
            onClick={() => setStatusFilter("")}
          >
            ✕ Clear
          </button>
        )}
      </div>

      {/* Quick Create Section */}
      <div style={{
        background: "#111111", border: "1px solid #1F1F1F",
        borderRadius: "12px", padding: "20px"
      }}>
        <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "14px" }}>
          Quick Create Reminder
        </h3>
        <p style={{ fontSize: "13px", color: "#777", marginBottom: "12px" }}>
          Select an application to create a follow-up reminder for.
        </p>
        {applications.length === 0 ? (
          <p style={{ fontSize: "13px", color: "#777" }}>No applications found.</p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", maxHeight: "200px", overflowY: "auto" }}>
            {applications.slice(0, 30).map((app) => (
              <div key={app.id} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "10px 12px", background: "#0B0B0B", borderRadius: "8px",
                fontSize: "12px"
              }}>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ color: "#fff", fontWeight: 500 }}>{app.role}</div>
                  <div style={{ color: "#777", fontSize: "11px" }}>{app.company}</div>
                  <div style={{ color: "#777", fontSize: "10px" }}>
                    {app.candidate?.name} — {app.candidate?.email}
                  </div>
                </div>
                <button
                  className="btn-outline-gold"
                  style={{ padding: "4px 10px", fontSize: "11px" }}
                  onClick={() => handleCreateReminder(app)}
                >
                  + Reminder
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upcoming Reminders */}
      <div>
        <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#fff", marginBottom: "12px" }}>
          Upcoming Reminders
        </h2>
        {loading ? (
          <div style={{ padding: "60px 24px", display: "flex", flexDirection: "column", alignItems: "center", gap: "16px" }}>
            <div className="spinner-gold" />
            <span style={{ color: "#777", fontSize: "14px" }}>Loading reminders...</span>
          </div>
        ) : upcomingReminders.length === 0 ? (
          <div style={{ padding: "40px 24px", textAlign: "center", background: "#111111", borderRadius: "12px", border: "1px solid #1F1F1F" }}>
            <div style={{ fontSize: "36px", marginBottom: "12px" }}>⏰</div>
            <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#fff", marginBottom: "6px" }}>
              No Upcoming Reminders
            </h3>
            <p style={{ color: "#777", fontSize: "13px" }}>
              All your reminders are complete. Use "Quick Create" above to schedule new ones.
            </p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="premium-table">
              <thead>
                <tr>
                  <th>Application</th>
                  <th>Type</th>
                  <th>Scheduled At</th>
                  <th>Lead Time</th>
                  <th>Message</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {upcomingReminders.map((r) => {
                  const app = r.application || {};
                  return (
                    <tr key={r.id}>
                      <td>
                        <div style={{ fontWeight: 600, color: "#fff", fontSize: "13px" }}>{app.role || "—"}</div>
                        <div style={{ fontSize: "11px", color: "#777" }}>{app.company || "—"}</div>
                      </td>
                      <td>
                        <span style={{
                          fontSize: "11px", padding: "2px 8px", borderRadius: "4px",
                          background: "rgba(212,175,55,0.1)", color: "#D4AF37"
                        }}>{r.reminder_type}</span>
                      </td>
                      <td style={{ fontSize: "12px" }}>
                        {r.scheduled_at ? new Date(r.scheduled_at).toLocaleString() : "—"}
                      </td>
                      <td style={{ fontSize: "12px", color: "#777" }}>
                        {r.lead_time_minutes > 0 ? `${r.lead_time_minutes} min` : "At time"}
                      </td>
                      <td style={{ fontSize: "12px", color: "#B8B8B8", maxWidth: "200px" }}>
                        {r.message ? (
                          <span title={r.message} style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", display: "block" }}>
                            {r.message}
                          </span>
                        ) : "—"}
                      </td>
                      <td>
                        <div style={{ display: "flex", gap: "6px" }}>
                          <button
                            style={{
                              padding: "4px 8px", fontSize: "11px",
                              background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)",
                              borderRadius: "6px", color: "#ef4444", cursor: "pointer"
                            }}
                            onClick={() => handleDismiss(r.id)}
                          >
                            Dismiss
                          </button>
                          <button
                            style={{
                              padding: "4px 8px", fontSize: "11px",
                              background: "rgba(255,215,0,0.08)", border: "1px solid rgba(255,215,0,0.2)",
                              borderRadius: "6px", color: "#D4AF37", cursor: "pointer"
                            }}
                            onClick={() => handleDelete(r.id)}
                          >
                            🗑
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Past Reminders */}
      {pastReminders.length > 0 && (
        <div>
          <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#fff", marginBottom: "12px" }}>
            Past Reminders ({pastReminders.length})
          </h2>
          <div style={{ overflowX: "auto" }}>
            <table className="premium-table">
              <thead>
                <tr>
                  <th>Application</th>
                  <th>Type</th>
                  <th>Scheduled At</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {pastReminders.slice(0, 50).map((r) => {
                  const app = r.application || {};
                  return (
                    <tr key={r.id}>
                      <td>
                        <div style={{ fontWeight: 500, color: "#fff" }}>{app.role || "—"}</div>
                        <div style={{ fontSize: "11px", color: "#777" }}>{app.company || "—"}</div>
                      </td>
                      <td style={{ fontSize: "12px" }}>{r.reminder_type}</td>
                      <td style={{ fontSize: "12px" }}>
                        {r.scheduled_at ? new Date(r.scheduled_at).toLocaleString() : "—"}
                      </td>
                      <td>
                        <span style={{
                          fontSize: "11px", padding: "2px 8px", borderRadius: "4px",
                          background: r.dismissed
                            ? "rgba(107,114,128,0.1)"
                            : r.status === "SENT"
                              ? "rgba(34,197,94,0.1)"
                              : "rgba(239,68,68,0.1)",
                          color: r.dismissed
                            ? "#6b7280"
                            : r.status === "SENT"
                              ? "#22c55e"
                              : "#ef4444"
                        }}>{r.status}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modals */}
      {modalOpen && selectedApp && (
        <ReminderModal
          app={selectedApp}
          onClose={() => setModalOpen(false)}
          onSuccess={() => {
            fetchReminders();
            fetchApplications();
          }}
        />
      )}
    </div>
  );
}
