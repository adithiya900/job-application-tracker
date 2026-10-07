import React, { useState, useEffect, useCallback } from "react";
import api from "../services/api";
import toast from "react-hot-toast";
import StatusBadge, { STATUS_CONFIG } from "../components/StatusBadge";

// HR can change to these statuses (NOT WITHDRAWN - that's candidate-only)
const HR_STATUS_OPTIONS = ["APPLIED", "UNDER_REVIEW", "PHONE_SCREEN", "INTERVIEW", "OFFER", "REJECTED"];

const STAT_CARDS = [
  { key: "APPLIED",      label: "Applied",       icon: "📝", accent: "#D4AF37" },
  { key: "UNDER_REVIEW", label: "Under Review",  icon: "🔍", accent: "#F5C542" },
  { key: "PHONE_SCREEN", label: "Phone Screen",  icon: "📞", accent: "#E8B84B" },
  { key: "INTERVIEW",    label: "Interview",     icon: "🎙", accent: "#FFD700" },
  { key: "OFFER",        label: "Offers",        icon: "🎉", accent: "#22c55e" },
  { key: "REJECTED",     label: "Rejected",      icon: "❌", accent: "#ef4444" },
  { key: "WITHDRAWN",    label: "Withdrawn",     icon: "↩", accent: "#6b7280" },
];

function Skeleton({ width = "100%", height = "20px" }) {
  return <div className="skeleton" style={{ width, height, borderRadius: "6px" }} />;
}

// ─── Status Update Modal ─────────────────────────────────────────────────────

function StatusModal({ app, onClose, onSuccess }) {
  const [newStatus, setNewStatus] = useState(app.status);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newStatus) return;
    setSaving(true);
    try {
      await api.patch(`/api/hr/applications/${app.id}/status`, { status: newStatus, notes }, { skipErrorHandler: true });
      toast.success(`Status updated to ${STATUS_CONFIG[newStatus]?.label || newStatus}`);
      onSuccess();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to update status");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: "460px" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">Update Status</div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#777", fontSize: "20px", cursor: "pointer" }}>✕</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ background: "#0B0B0B", borderRadius: "8px", padding: "12px 14px" }}>
              <div style={{ fontSize: "12px", color: "#777", marginBottom: "2px" }}>Candidate</div>
              <div style={{ fontWeight: 600, color: "#fff" }}>{app.candidate?.name}</div>
              <div style={{ fontSize: "12px", color: "#B8B8B8" }}>{app.role} at {app.company}</div>
            </div>

            <div>
              <div style={{ fontSize: "12px", color: "#777", marginBottom: "4px" }}>Current Status</div>
              <StatusBadge status={app.status} />
            </div>

            <div>
              <label className="label-gold">New Status</label>
              <select
                className="input-gold"
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                required
              >
                {HR_STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>{STATUS_CONFIG[s]?.label || s}</option>
                ))}
              </select>
              <p style={{ fontSize: "11px", color: "#777", marginTop: "4px" }}>
                Note: WITHDRAWN status is controlled by candidates only.
              </p>
            </div>

            <div>
              <label className="label-gold">Notes (Optional)</label>
              <textarea
                className="input-gold"
                rows={3}
                placeholder="Reason or notes for status change..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                style={{ resize: "vertical" }}
              />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn-outline-gold" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-gold" disabled={saving}>
              {saving ? "Saving..." : "Save & Notify Candidate"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Schedule Interview Modal ─────────────────────────────────────────────────

function InterviewModal({ app, onClose, onSuccess }) {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [round, setRound] = useState("Technical Round 1");
  const [type, setType] = useState("Online");
  const [link, setLink] = useState("");
  const [interviewer, setInterviewer] = useState("");
  const [hrNotes, setHrNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch(`/api/hr/applications/${app.id}/interview`, {
        interview_date: date || null,
        interview_time: time || null,
        interview_round: round,
        interview_type: type,
        meeting_link: link,
        interviewer,
        hr_notes: hrNotes,
      }, { skipErrorHandler: true });
      toast.success("Interview scheduled & candidate notified!");
      onSuccess(); onClose();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to schedule interview");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: "560px" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">Schedule Interview</div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#777", fontSize: "20px", cursor: "pointer" }}>✕</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ background: "#0B0B0B", borderRadius: "8px", padding: "12px 14px" }}>
              <div style={{ fontWeight: 600, color: "#fff" }}>{app.candidate?.name}</div>
              <div style={{ fontSize: "12px", color: "#B8B8B8" }}>{app.role} at {app.company}</div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
              <div>
                <label className="label-gold">Date *</label>
                <input type="date" className="input-gold" value={date} onChange={(e) => setDate(e.target.value)} required />
              </div>
              <div>
                <label className="label-gold">Time *</label>
                <input type="time" className="input-gold" value={time} onChange={(e) => setTime(e.target.value)} required />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
              <div>
                <label className="label-gold">Round</label>
                <select className="input-gold" value={round} onChange={(e) => setRound(e.target.value)}>
                  <option value="Technical Round 1">Technical Round 1</option>
                  <option value="Technical Round 2">Technical Round 2</option>
                  <option value="HR Round">HR Round</option>
                  <option value="Managerial Round">Managerial Round</option>
                  <option value="Final Round">Final Round</option>
                </select>
              </div>
              <div>
                <label className="label-gold">Interview Type</label>
                <select className="input-gold" value={type} onChange={(e) => setType(e.target.value)}>
                  <option value="Online">Online Video Call</option>
                  <option value="Phone Screen">Phone Screen</option>
                  <option value="In-person">In-person</option>
                </select>
              </div>
            </div>

            <div>
              <label className="label-gold">Meeting Link</label>
              <input type="url" className="input-gold" placeholder="https://meet.google.com/..." value={link} onChange={(e) => setLink(e.target.value)} />
            </div>

            <div>
              <label className="label-gold">Interviewer Name</label>
              <input type="text" className="input-gold" placeholder="e.g. John Doe (Engineering Lead)" value={interviewer} onChange={(e) => setInterviewer(e.target.value)} />
            </div>

            <div>
              <label className="label-gold">
                🔒 HR Internal Notes
                <span style={{ fontSize: "10px", color: "#777", fontWeight: 400, marginLeft: "6px" }}>(Not visible to candidate)</span>
              </label>
              <textarea className="input-gold" rows={2} placeholder="Private preparation notes..." value={hrNotes} onChange={(e) => setHrNotes(e.target.value)} style={{ resize: "vertical" }} />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn-outline-gold" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-gold" disabled={saving}>
              {saving ? "Scheduling..." : "Schedule & Notify"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Feedback Modal ───────────────────────────────────────────────────────────

function FeedbackModal({ app, onClose, onSuccess }) {
  const [techSkills, setTechSkills] = useState("Good");
  const [commSkills, setCommSkills] = useState("Good");
  const [overall, setOverall] = useState("");
  const [recommendation, setRecommendation] = useState("Hire");
  const [internalNotes, setInternalNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/api/hr/applications/${app.id}/feedback`, {
        technical_skills: techSkills,
        communication: commSkills,
        overall_feedback: overall,
        recommendation,
        internal_notes: internalNotes,
      }, { skipErrorHandler: true });
      toast.success("Interview feedback recorded!");
      onSuccess(); onClose();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to submit feedback");
    } finally {
      setSaving(false);
    }
  };

  const RatingSelect = ({ label, value, onChange, options }) => (
    <div>
      <label className="label-gold">{label}</label>
      <select className="input-gold" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: "480px" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">Interview Feedback</div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#777", fontSize: "20px", cursor: "pointer" }}>✕</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ background: "#0B0B0B", borderRadius: "8px", padding: "12px 14px" }}>
              <div style={{ fontWeight: 600, color: "#fff" }}>{app.candidate?.name}</div>
              <div style={{ fontSize: "12px", color: "#B8B8B8" }}>{app.role} at {app.company}</div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
              <RatingSelect label="Technical Skills" value={techSkills} onChange={setTechSkills}
                options={["Excellent", "Good", "Average", "Below Average"]} />
              <RatingSelect label="Communication" value={commSkills} onChange={setCommSkills}
                options={["Excellent", "Good", "Average", "Needs Improvement"]} />
            </div>

            <div>
              <label className="label-gold">Recommendation</label>
              <div style={{ display: "flex", gap: "10px" }}>
                {["Hire", "Maybe", "No Hire"].map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRecommendation(r)}
                    style={{
                      flex: 1, padding: "10px 0", borderRadius: "8px", cursor: "pointer",
                      fontSize: "13px", fontWeight: 600, transition: "all 0.2s",
                      background: recommendation === r
                        ? (r === "Hire" ? "rgba(34,197,94,0.2)" : r === "Maybe" ? "rgba(255,215,0,0.2)" : "rgba(239,68,68,0.2)")
                        : "rgba(255,255,255,0.04)",
                      border: recommendation === r
                        ? (r === "Hire" ? "1px solid rgba(34,197,94,0.5)" : r === "Maybe" ? "1px solid rgba(255,215,0,0.5)" : "1px solid rgba(239,68,68,0.5)")
                        : "1px solid #2A2A2A",
                      color: recommendation === r
                        ? (r === "Hire" ? "#22c55e" : r === "Maybe" ? "#FFD700" : "#ef4444")
                        : "#777"
                    }}
                  >
                    {r === "Hire" ? "✅ " : r === "Maybe" ? "🤔 " : "❌ "}{r}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label-gold">Overall Feedback</label>
              <textarea
                className="input-gold" rows={3}
                placeholder="Detailed candidate evaluation..."
                value={overall} onChange={(e) => setOverall(e.target.value)}
                style={{ resize: "vertical" }}
              />
            </div>

            <div>
              <label className="label-gold">
                🔒 Internal Notes
                <span style={{ fontSize: "10px", color: "#777", fontWeight: 400, marginLeft: "6px" }}>(HR only — never shown to candidate)</span>
              </label>
              <textarea
                className="input-gold" rows={2}
                placeholder="Compensation discussion, internal concerns..."
                value={internalNotes} onChange={(e) => setInternalNotes(e.target.value)}
                style={{ resize: "vertical" }}
              />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn-outline-gold" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-gold" disabled={saving}>
              {saving ? "Submitting..." : "Submit Feedback"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── App Detail Modal (HR) ────────────────────────────────────────────────────

function HRDetailModal({ app, onClose }) {
  if (!app) return null;
  const feedbackEntries = Array.isArray(app.feedback)
    ? app.feedback
    : app.feedback
      ? [app.feedback]
      : [];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: "680px" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="modal-title">{app.role} at {app.company}</div>
            <div style={{ fontSize: "13px", color: "#777", marginTop: "2px" }}>Application Timeline</div>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#777", fontSize: "20px", cursor: "pointer" }}>✕</button>
        </div>

        <div className="modal-body" style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Candidate Info */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", background: "#0B0B0B", borderRadius: "10px", padding: "16px" }}>
            <div>
              <div style={{ fontSize: "11px", color: "#777", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>Candidate</div>
              <div style={{ fontWeight: 700, color: "#fff", fontSize: "15px" }}>{app.candidate?.name}</div>
              <div style={{ fontSize: "12px", color: "#B8B8B8", marginTop: "2px" }}>{app.candidate?.email}</div>
            </div>
            <div>
              <div style={{ fontSize: "11px", color: "#777", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>Current Status</div>
              <StatusBadge status={app.status} />
            </div>
            <div>
              <div style={{ fontSize: "11px", color: "#777", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>Applied</div>
              <div style={{ color: "#E8E8E8", fontSize: "13px" }}>
                {app.applied_date ? new Date(app.applied_date).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—"}
              </div>
            </div>
            {app.resume_path && (
              <div>
                <div style={{ fontSize: "11px", color: "#777", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>Resume</div>
                <div style={{ fontSize: "12px", color: "#D4AF37" }}>📄 {app.resume_path.split(/[\\/]/).pop()}</div>
              </div>
            )}
          </div>

          {/* Interview Details */}
          {app.interview_details && (
            <div style={{
              background: "rgba(255,215,0,0.05)", border: "1px solid rgba(255,215,0,0.2)",
              borderRadius: "10px", padding: "16px"
            }}>
              <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#FFD700", marginBottom: "14px" }}>
                🎙 Scheduled Interview
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "13px" }}>
                {[
                  ["Round", app.interview_details.interview_round],
                  ["Type", app.interview_details.interview_type],
                  ["Date", app.interview_details.interview_date],
                  ["Time", app.interview_details.interview_time],
                  ["Interviewer", app.interview_details.interviewer],
                ].map(([label, val]) => val ? (
                  <div key={label}>
                    <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>{label}</div>
                    <div style={{ color: "#E8E8E8", fontWeight: 500 }}>{val}</div>
                  </div>
                ) : null)}
                {app.interview_details.meeting_link && (
                  <div style={{ gridColumn: "1/-1" }}>
                    <a href={app.interview_details.meeting_link} target="_blank" rel="noreferrer"
                      style={{ color: "#D4AF37", fontSize: "12px", textDecoration: "underline" }}>
                      🔗 {app.interview_details.meeting_link}
                    </a>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Status Timeline */}
          <div>
            <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#FFD700", marginBottom: "14px" }}>Status History</h3>
            {app.status_history && app.status_history.length > 0 ? (
              <div className="timeline">
                {app.status_history.map((h, i) => (
                  <div key={h.id || i} className="timeline-item">
                    <div className="timeline-dot" />
                    <div style={{ fontSize: "13px", fontWeight: 600, color: "#E8E8E8" }}>
                      {h.old_status
                        ? `${STATUS_CONFIG[h.old_status]?.label || h.old_status} → ${STATUS_CONFIG[h.new_status]?.label || h.new_status}`
                        : `Application Created (${STATUS_CONFIG[h.new_status]?.label || h.new_status})`}
                    </div>
                    <div style={{ fontSize: "11px", color: "#777", marginTop: "2px" }}>
                      {new Date(h.changed_at).toLocaleString()} {h.changed_by_name ? `by ${h.changed_by_name}` : ""}
                    </div>
                    {h.notes && (
                      <div style={{ fontSize: "12px", color: "#B8B8B8", background: "#0B0B0B", borderRadius: "6px", padding: "8px 10px", marginTop: "6px", fontStyle: "italic" }}>
                        {h.notes}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: "13px", color: "#777" }}>No history recorded yet.</p>
            )}
          </div>

          {/* Feedback */}
          {feedbackEntries.length > 0 && (
            <div style={{
              background: "#0B0B0B", border: "1px solid #1F1F1F",
              borderRadius: "10px", padding: "16px"
            }}>
              <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#FFD700", marginBottom: "14px" }}>Interview Feedback</h3>
              {feedbackEntries.map((feedback, index) => (
                <div key={feedback.id || index} style={{ marginTop: index ? "16px" : 0 }}>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: "12px", fontSize: "13px" }}>
                    <div>
                      <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>Technical</div>
                      <div style={{ color: "#E8E8E8", fontWeight: 500 }}>{feedback.technical_skills || "—"}</div>
                    </div>
                    <div>
                      <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>Communication</div>
                      <div style={{ color: "#E8E8E8", fontWeight: 500 }}>{feedback.communication || "—"}</div>
                    </div>
                    <div>
                      <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>Recommendation</div>
                      <div style={{ fontWeight: 600, color: feedback.recommendation === "Hire" ? "#22c55e" : feedback.recommendation === "No Hire" ? "#ef4444" : "#FFD700" }}>
                        {feedback.recommendation || "—"}
                      </div>
                    </div>
                  </div>
                  {feedback.overall_feedback && (
                    <div style={{ marginTop: "12px", fontSize: "13px", color: "#B8B8B8" }}>
                      {feedback.overall_feedback}
                    </div>
                  )}
                  {feedback.internal_notes && (
                    <div style={{
                      marginTop: "12px", background: "rgba(255,215,0,0.04)",
                      border: "1px solid rgba(255,215,0,0.15)", borderRadius: "8px",
                      padding: "10px 12px"
                    }}>
                      <div style={{ fontSize: "11px", color: "#777", marginBottom: "4px" }}>🔒 Internal Notes (HR Only)</div>
                      <div style={{ fontSize: "13px", color: "#D4AF37" }}>{feedback.internal_notes}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-outline-gold" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

// ─── HR Dashboard ─────────────────────────────────────────────────────────────

export default function HRDashboard() {
  const [applications, setApplications] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const [selectedApp, setSelectedApp] = useState(null);
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [interviewModalOpen, setInterviewModalOpen] = useState(false);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);

  const fetchHRApplications = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (statusFilter) params.set("status", statusFilter);
      const res = await api.get(`/api/hr/applications?${params}`, { skipErrorHandler: true });
      setApplications(res.data.applications || []);
      setStats(res.data.stats || {});
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to fetch applications");
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => {
    document.title = "HR Portal — Job Tracker";
    fetchHRApplications();
  }, [fetchHRApplications]);

  const fetchDetail = async (appId) => {
    try {
      const res = await api.get(`/api/hr/applications/${appId}`, { skipErrorHandler: true });
      setSelectedApp(res.data);
      setDetailModalOpen(true);
    } catch {
      toast.error("Failed to load application details");
    }
  };

  const totalApplications = Object.values(stats).reduce((a, b) => a + (b || 0), 0);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#fff", marginBottom: "6px" }}>
          HR Portal 👔
        </h1>
        <p style={{ color: "#777", fontSize: "14px" }}>
          Manage applications and find the best talent.
        </p>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))", gap: "12px" }}>
        {/* Total card */}
        <div
          className={`stat-card ${statusFilter === "" ? "active" : ""}`}
          onClick={() => setStatusFilter("")}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
            <span style={{ fontSize: "18px" }}>📊</span>
          </div>
          <div style={{ fontSize: "30px", fontWeight: 800, color: "#FFD700", lineHeight: 1 }}>
            {loading ? <Skeleton width="40px" height="28px" /> : totalApplications}
          </div>
          <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>Total</div>
        </div>

        {STAT_CARDS.map((card) => (
          <div
            key={card.key}
            className={`stat-card ${statusFilter === card.key ? "active" : ""}`}
            onClick={() => setStatusFilter(statusFilter === card.key ? "" : card.key)}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
              <span style={{ fontSize: "18px" }}>{card.icon}</span>
            </div>
            {loading ? (
              <Skeleton width="40px" height="28px" />
            ) : (
              <div style={{ fontSize: "30px", fontWeight: 800, color: card.accent, lineHeight: 1 }}>
                {stats[card.key] || 0}
              </div>
            )}
            <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>{card.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{
        background: "#111111", border: "1px solid #1F1F1F",
        borderRadius: "12px", padding: "16px 20px",
        display: "flex", gap: "14px", flexWrap: "wrap", alignItems: "flex-end"
      }}>
        <div style={{ flex: "2 1 220px", minWidth: "180px" }}>
          <label className="label-gold">Search</label>
          <div style={{ position: "relative" }}>
            <span style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "#777", fontSize: "14px" }}>🔍</span>
            <input
              className="input-gold"
              placeholder="Candidate, company, role..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: "36px" }}
            />
          </div>
        </div>

        <div style={{ flex: "1 1 160px", minWidth: "140px" }}>
          <label className="label-gold">Status Filter</label>
          <select
            className="input-gold"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            {Object.keys(STATUS_CONFIG).map((s) => (
              <option key={s} value={s}>{STATUS_CONFIG[s].label}</option>
            ))}
          </select>
        </div>

        {(statusFilter || search) && (
          <button
            className="btn-outline-gold"
            style={{ padding: "8px 14px", fontSize: "13px", alignSelf: "flex-end" }}
            onClick={() => { setStatusFilter(""); setSearch(""); }}
          >
            ✕ Clear
          </button>
        )}
      </div>

      {/* Table */}
      <div style={{
        background: "#111111", border: "1px solid #1F1F1F",
        borderRadius: "12px", overflow: "hidden"
      }}>
        <div style={{ overflowX: "auto" }}>
          {loading ? (
            <div style={{ padding: "60px 24px", display: "flex", flexDirection: "column", alignItems: "center", gap: "20px" }}>
              <div className="spinner-gold" />
              <span style={{ color: "#777", fontSize: "14px" }}>Loading applications...</span>
            </div>
          ) : applications.length === 0 ? (
            <div style={{ padding: "80px 24px", textAlign: "center" }}>
              <div style={{ fontSize: "48px", marginBottom: "16px" }}>👥</div>
              <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#fff", marginBottom: "8px" }}>
                No Applications Found
              </h3>
              <p style={{ color: "#777", fontSize: "14px", marginBottom: "20px" }}>
                Applications matching your filters will appear here.
              </p>
              {(statusFilter || search) && (
                <button
                  className="btn-outline-gold"
                  onClick={() => { setStatusFilter(""); setSearch(""); }}
                >
                  Clear Filters
                </button>
              )}
            </div>
          ) : (
            <table className="premium-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Company</th>
                  <th>Job Role</th>
                  <th>Status</th>
                  <th>Applied Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((app) => (
                  <tr key={app.id}>
                    <td>
                      <div style={{ fontWeight: 600, color: "#fff", fontSize: "14px" }}>{app.candidate?.name || "Candidate"}</div>
                      <div style={{ fontSize: "11px", color: "#777" }}>{app.candidate?.email}</div>
                    </td>
                    <td>{app.company}</td>
                    <td>{app.role}</td>
                    <td><StatusBadge status={app.status} /></td>
                    <td style={{ fontSize: "12px" }}>
                      {app.applied_date ? new Date(app.applied_date).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—"}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                        <button
                          style={{
                            padding: "5px 10px", fontSize: "11px", fontWeight: 600,
                            background: "rgba(255,215,0,0.08)", border: "1px solid rgba(255,215,0,0.2)",
                            borderRadius: "6px", color: "#D4AF37", cursor: "pointer",
                            transition: "all 0.2s"
                          }}
                          onClick={() => { setSelectedApp(app); setNewStatusFor(app); setStatusModalOpen(true); }}
                        >
                          Status
                        </button>
                        <button
                          style={{
                            padding: "5px 10px", fontSize: "11px", fontWeight: 600,
                            background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.2)",
                            borderRadius: "6px", color: "#22c55e", cursor: "pointer",
                          }}
                          onClick={() => { setSelectedApp(app); setInterviewModalOpen(true); }}
                        >
                          Interview
                        </button>
                        <button
                          style={{
                            padding: "5px 10px", fontSize: "11px", fontWeight: 600,
                            background: "rgba(139,92,246,0.08)", border: "1px solid rgba(139,92,246,0.2)",
                            borderRadius: "6px", color: "#a78bfa", cursor: "pointer",
                          }}
                          onClick={() => { setSelectedApp(app); setFeedbackModalOpen(true); }}
                        >
                          Feedback
                        </button>
                        <button
                          style={{
                            padding: "5px 10px", fontSize: "11px", fontWeight: 600,
                            background: "rgba(255,255,255,0.04)", border: "1px solid #2A2A2A",
                            borderRadius: "6px", color: "#B8B8B8", cursor: "pointer",
                          }}
                          onClick={() => fetchDetail(app.id)}
                        >
                          Timeline
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modals */}
      {statusModalOpen && selectedApp && (
        <StatusModal
          app={selectedApp}
          onClose={() => setStatusModalOpen(false)}
          onSuccess={fetchHRApplications}
        />
      )}

      {interviewModalOpen && selectedApp && (
        <InterviewModal
          app={selectedApp}
          onClose={() => setInterviewModalOpen(false)}
          onSuccess={fetchHRApplications}
        />
      )}

      {feedbackModalOpen && selectedApp && (
        <FeedbackModal
          app={selectedApp}
          onClose={() => setFeedbackModalOpen(false)}
          onSuccess={fetchHRApplications}
        />
      )}

      {detailModalOpen && selectedApp && (
        <HRDetailModal
          app={selectedApp}
          onClose={() => setDetailModalOpen(false)}
        />
      )}
    </div>
  );
}

// Helper to avoid error (not needed but keeps code clean)
function setNewStatusFor() {}
