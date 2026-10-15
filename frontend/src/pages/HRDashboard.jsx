import { useState, useEffect, useCallback } from "react";
import api from "../services/api";
import toast from "react-hot-toast";
import StatusBadge, { STATUS_CONFIG } from "../components/StatusBadge";
const HR_STATUS_OPTIONS = ["APPLIED", "UNDER_REVIEW", "PHONE_CALL", "INTERVIEW", "OFFER", "REJECTED"];

const STAT_CARDS = [
  { key: "APPLIED",      label: "Applied",       icon: "📝", accent: "#D4AF37" },
  { key: "UNDER_REVIEW", label: "Under Review",  icon: "🔍", accent: "#F5C542" },
  { key: "PHONE_CALL", label: "Phone Call",  icon: "📞", accent: "#E8B84B" },
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
  const isDisabled = !app?.candidate?.is_active;

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
              <div style={{ fontSize: "12px", color: "#B8B8B8" }}>{app.candidate?.email}</div>
              {app.candidate?.phone_number && (
                <div style={{ fontSize: "12px", color: "#B8B8B8" }}>{app.candidate.phone_number}</div>
              )}
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
                disabled={isDisabled}
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
                disabled={isDisabled}
              />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn-outline-gold" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-gold" disabled={saving || isDisabled}>
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
  const [roundType, setRoundType] = useState("");
  const [type, setType] = useState("Online");
  const [link, setLink] = useState("");
  const [interviewer, setInterviewer] = useState("");
  const [hrNotes, setHrNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const isDisabled = !app?.candidate?.is_active;

  const handleTypeChange = (e) => {
    const next = e.target.value;
    setType(next);
    if (next !== "Online") {
      setLink("");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch(`/api/hr/applications/${app.id}/interview`, {
        interview_date: date || null,
        interview_time: time || null,
        interview_round: round,
        round_type: round === "Custom" ? roundType : round,
        interview_type: type,
        meeting_link: type === "Online" ? link : null,
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
                  <option value="Phone Screen">Phone Screen</option>
                  <option value="Technical Round 1">Technical Round 1</option>
                  <option value="Technical Round 2">Technical Round 2</option>
                  <option value="HR Round">HR Round</option>
                  <option value="Managerial Round">Managerial Round</option>
                  <option value="Final Round">Final Round</option>
                  <option value="Custom">Custom</option>
                </select>
              </div>
              {round === "Custom" && (
                <div>
                  <label className="label-gold">Round Type</label>
                  <input type="text" className="input-gold" placeholder="e.g. Coding Challenge" value={roundType} onChange={(e) => setRoundType(e.target.value)} />
                </div>
              )}
              <div>
                <label className="label-gold">Interview Type</label>
                <select className="input-gold" value={type} onChange={handleTypeChange}>
                  <option value="Online">Online Video Call</option>
                  <option value="Phone Screen">Phone Screen</option>
                  <option value="In-person">In-person</option>
                </select>
              </div>
            </div>

            {type === "Online" && (
              <div>
                <label className="label-gold">Meeting Link *</label>
                <input type="url" className="input-gold" placeholder="https://meet.google.com/..." value={link} onChange={(e) => setLink(e.target.value)} required />
              </div>
            )}

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
            <button type="submit" className="btn-gold" disabled={saving || isDisabled}>
              {saving ? "Scheduling..." : "Schedule & Notify"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Feedback Modal ───────────────────────────────────────────────────────────

function RatingSelect({ label, value, onChange, options, disabled }) {
  return (
    <div>
      <label className="label-gold">{label}</label>
      <select className="input-gold" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled}>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

function FeedbackModal({ app, onClose, onSuccess }) {
  const [techSkills, setTechSkills] = useState("Good");
  const [commSkills, setCommSkills] = useState("Good");
  const [rating, setRating] = useState(3);
  const [strengths, setStrengths] = useState("");
  const [weaknesses, setWeaknesses] = useState("");
  const [overall, setOverall] = useState("");
  const [candidateFacing, setCandidateFacing] = useState(false);
  const [candidateSummary, setCandidateSummary] = useState("");
  const [recommendation, setRecommendation] = useState("Hire");
  const [internalNotes, setInternalNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const isDisabled = !app?.candidate?.is_active;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/api/hr/applications/${app.id}/feedback`, {
        technical_skills: techSkills,
        communication: commSkills,
        rating,
        strengths: strengths || null,
        weaknesses: weaknesses || null,
        candidate_facing: candidateFacing,
        candidate_facing_summary: candidateSummary || null,
        overall_feedback: overall || null,
        recommendation,
        internal_notes: internalNotes || null,
      }, { skipErrorHandler: true });
      toast.success("Interview feedback recorded!");
      onSuccess(); onClose();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to submit feedback");
    } finally {
      setSaving(false);
    }
  };

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
              {!app.candidate?.is_active && (
                <div style={{ marginTop: "8px", fontSize: "12px", color: "#ef4444", fontWeight: 600 }}>
                  This candidate account is disabled.
                </div>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
              <RatingSelect label="Technical Skills" value={techSkills} onChange={setTechSkills}
                options={["Excellent", "Good", "Average", "Below Average"]} disabled={isDisabled} />
              <RatingSelect label="Communication" value={commSkills} onChange={setCommSkills}
                options={["Excellent", "Good", "Average", "Needs Improvement"]} disabled={isDisabled} />
            </div>

            <div>
              <label className="label-gold">Rating (1-5)</label>
              <select className="input-gold" value={rating} onChange={(e) => setRating(parseInt(e.target.value))} disabled={isDisabled}>
                {[5, 4, 3, 2, 1].map((r) => (
                  <option key={r} value={r}>
                    {"★".repeat(r)}{"☆".repeat(5 - r)} ({r})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label-gold">Strengths</label>
              <textarea
                className="input-gold" rows={2}
                placeholder="What did the candidate do well? (e.g., problem-solving, communication)"
                value={strengths} onChange={(e) => setStrengths(e.target.value)}
                style={{ resize: "vertical" }}
                disabled={isDisabled}
                maxLength={1000}
              />
            </div>

            <div>
              <label className="label-gold">Weaknesses</label>
              <textarea
                className="input-gold" rows={2}
                placeholder="Areas for improvement..."
                value={weaknesses} onChange={(e) => setWeaknesses(e.target.value)}
                style={{ resize: "vertical" }}
                disabled={isDisabled}
                maxLength={1000}
              />
            </div>

            <div>
              <label className="label-gold">Recommendation</label>
              <div style={{ display: "flex", gap: "10px" }}>
                {["Hire", "Maybe", "No Hire"].map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRecommendation(r)}
                    disabled={isDisabled}
                    style={{
                      flex: 1, padding: "10px 0", borderRadius: "8px", cursor: isDisabled ? "not-allowed" : "pointer",
                      fontSize: "13px", fontWeight: 600, transition: "all 0.2s",
                      background: recommendation === r
                        ? (r === "Hire" ? "rgba(34,197,94,0.2)" : r === "Maybe" ? "rgba(255,215,0,0.2)" : "rgba(239,68,68,0.2)")
                        : "rgba(255,255,255,0.04)",
                      border: recommendation === r
                        ? (r === "Hire" ? "1px solid rgba(34,197,94,0.5)" : r === "Maybe" ? "1px solid rgba(255,215,0,0.5)" : "1px solid rgba(239,68,68,0.5)")
                        : "1px solid #2A2A2A",
                      color: recommendation === r
                        ? (r === "Hire" ? "#22c55e" : r === "Maybe" ? "#FFD700" : "#ef4444")
                        : "#777",
                      opacity: isDisabled ? 0.6 : 1,
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
                disabled={isDisabled}
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
                disabled={isDisabled}
              />
            </div>

            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <input
                  type="checkbox"
                  id="candidateFacingCheckbox"
                  checked={candidateFacing}
                  onChange={(e) => setCandidateFacing(e.target.checked)}
                  disabled={isDisabled}
                  style={{ accentColor: "#D4AF37" }}
                />
                <label className="label-gold" htmlFor="candidateFacingCheckbox">Share summary with candidate</label>
              </div>
              {candidateFacing && (
                <textarea
                  className="input-gold" rows={2}
                  placeholder="Candidate-facing summary..."
                  value={candidateSummary} onChange={(e) => setCandidateSummary(e.target.value)}
                  style={{ resize: "vertical", marginTop: "8px" }}
                  disabled={isDisabled}
                  maxLength={500}
                />
              )}
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn-outline-gold" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-gold" disabled={saving || isDisabled}>
              {saving ? "Submitting..." : "Submit Feedback"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Message Modal (HR → Candidate) ─────────────────────────────────────────────

function MessageModal({ app, onClose, onSuccess }) {
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;
    setSubmitting(true);
    try {
      await api.post(`/api/hr/applications/${app.id}/notify`, {
        message: message.trim(),
        type: "HR_MESSAGE",
      }, { skipErrorHandler: true });
      toast.success("Message sent to candidate!");
      onSuccess();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to send message");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: "500px" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="modal-title">Message Candidate</div>
            <div style={{ fontSize: "13px", color: "#777", marginTop: "2px" }}>{app.candidate?.name}</div>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#777", fontSize: "20px", cursor: "pointer" }}>✕</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div style={{ marginBottom: "12px" }}>
              <div style={{ fontSize: "12px", color: "#777", marginBottom: "6px" }}>Candidate</div>
              <div style={{ fontWeight: 600, color: "#fff" }}>{app.candidate?.name}</div>
              <div style={{ fontSize: "12px", color: "#B8B8B8" }}>{app.role} at {app.company}</div>
            </div>
            <div>
              <label className="label-gold">Message</label>
              <textarea
                className="input-gold"
                rows={4}
                placeholder="Type your message here..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                required
                style={{ resize: "vertical" }}
                maxLength={500}
              />
              <div style={{ fontSize: "11px", color: "#777", marginTop: "4px" }}>
                {message.length}/500 characters
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn-outline-gold" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-gold" disabled={submitting || !message.trim()}>
              {submitting ? "Sending..." : "Send Message"}
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
  const isDisabled = !app?.candidate?.is_active;

  const downloadResume = async (appId) => {
    try {
      const response = await api.get(`/api/hr/applications/${appId}/resume`, {
        responseType: "blob",
        skipErrorHandler: true,
      });
      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = app.resume_path.split(/[\\/]/).pop() || "resume.pdf";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      // With responseType "blob" the error body is a Blob, so axios cannot
      // parse it and err.response.data.error is undefined. Read it back so the
      // reviewer sees the real reason instead of a raw status code.
      let message = err.message;
      const data = err.response?.data;
      if (data instanceof Blob) {
        try {
          const parsed = JSON.parse(await data.text());
          message = parsed.error || parsed.message || message;
        } catch {
          message = "The resume file could not be found.";
        }
      } else if (err.response?.data?.error) {
        message = err.response.data.error;
      }
      toast.error("Failed to download resume: " + message);
    }
  };

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

        {isDisabled && (
          <div style={{
            background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)",
            borderRadius: "10px", padding: "12px 16px", color: "#ef4444", fontSize: "13px", fontWeight: 600
          }}>
            This candidate account is disabled.
          </div>
        )}

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
                <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px" }}>
                  <button
                    onClick={() => downloadResume(app.id)}
                    style={{
                      padding: "4px 12px", fontSize: "11px",
                      background: "transparent", border: "1px solid rgba(255,215,0,0.2)",
                      borderRadius: "6px", color: "#D4AF37", cursor: "pointer"
                    }}
                  >
                    📄 View / Download Resume
                  </button>
                  <span style={{ fontSize: "10px", color: "#555" }}>{app.resume_path.split(/[\\/]/).pop()}</span>
                </div>
              </div>
            )}
          </div>

           {/* Interview Details (Multiple Rounds) */}
           {app.interview_details && app.interview_details.length > 0 && (
             <div style={{
               background: "rgba(255,215,0,0.05)", border: "1px solid rgba(255,215,0,0.2)",
               borderRadius: "10px", padding: "16px"
             }}>
               <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#FFD700", marginBottom: "14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                 🎙 Scheduled Interviews ({app.interview_details.length})
               </h3>
               {app.interview_details.map((interview, idx) => (
                 <div key={interview.id || idx} style={{
                   marginBottom: idx < app.interview_details.length - 1 ? "16px" : "0",
                   padding: idx < app.interview_details.length - 1 ? "12px 14px" : "12px 14px",
                   background: "#0B0B0B", borderRadius: "8px"
                 }}>
                   <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                     <div style={{ fontSize: "13px", fontWeight: 600, color: "#fff" }}>
                       {interview.interview_round || `Round ${idx + 1}`}
                     </div>
                     {interview.interview_type === "Online" && interview.meeting_link && (
                       <a href={interview.meeting_link} target="_blank" rel="noreferrer"
                         style={{ color: "#D4AF37", fontSize: "11px", textDecoration: "underline" }}>
                         🔗 Join
                       </a>
                     )}
                   </div>
                   <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "12px" }}>
                     {[
                       ["Type", interview.interview_type],
                       ["Round Type", interview.round_type],
                       ["Date", interview.interview_date],
                       ["Time", interview.interview_time],
                       ["Interviewer", interview.interviewer],
                     ].map(([label, val]) => val ? (
                       <div key={label}>
                         <span style={{ color: "#777" }}>{label}: </span>
                         <span style={{ color: "#B8B8B8" }}>{val}</span>
                       </div>
                     ) : null)}
                   </div>
                   {interview.meeting_link && interview.interview_type !== "Online" && (
                     <div style={{ marginTop: "6px" }}>
                       <a href={interview.meeting_link} target="_blank" rel="noreferrer"
                         style={{ color: "#D4AF37", fontSize: "11px", textDecoration: "underline" }}>
                         🔗 {interview.meeting_link}
                       </a>
                     </div>
                   )}
                 </div>
               ))}
               <div style={{ marginTop: "12px", display: "flex", gap: "8px" }}>
                 <button
                   style={{ padding: "4px 10px", fontSize: "11px", background: "rgba(255,215,0,0.1)", border: "1px solid rgba(255,215,0,0.3)", borderRadius: "6px", color: "#D4AF37", cursor: "pointer" }}
                   onClick={() => window.open(`/api/hr/applications/${app.id}/calendar`, "_blank")}
                 >
                   📅 Export Calendar (.ics)
                 </button>
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
                   <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "10px" }}>
                     <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: "12px", fontSize: "13px" }}>
                       <div>
                         <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>Technical</div>
                         <div style={{ color: "#E8E8E8", fontWeight: 500 }}>{feedback.technical_skills || "—"}</div>
                       </div>
                       <div>
                         <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>Communication</div>
                         <div style={{ color: "#E8E8E8", fontWeight: 500 }}>{feedback.communication || "—"}</div>
                       </div>
                       {feedback.rating && (
                         <div>
                           <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>Rating</div>
                           <div style={{ color: "#FFD700", fontWeight: 500 }}>
                             {"★".repeat(feedback.rating)}{"☆".repeat(5 - feedback.rating)}
                           </div>
                         </div>
                       )}
                       <div>
                         <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>Recommendation</div>
                         <div style={{ fontWeight: 600, color: feedback.recommendation === "Hire" ? "#22c55e" : feedback.recommendation === "No Hire" ? "#ef4444" : "#FFD700" }}>
                           {feedback.recommendation || "—"}
                         </div>
                       </div>
                     </div>
                     {feedback.created_at && (
                       <div style={{ fontSize: "10px", color: "#555", textAlign: "right" }}>
                         {new Date(feedback.created_at).toLocaleDateString()}
                       </div>
                     )}
                   </div>
                   {feedback.strengths && (
                     <div style={{ marginBottom: "8px" }}>
                       <div style={{ fontSize: "10px", color: "#22c55e", fontWeight: 600, marginBottom: "2px" }}>Strengths</div>
                       <div style={{ fontSize: "12px", color: "#B8B8B8" }}>{feedback.strengths}</div>
                     </div>
                   )}
                   {feedback.weaknesses && (
                     <div style={{ marginBottom: "8px" }}>
                       <div style={{ fontSize: "10px", color: "#ef4444", fontWeight: 600, marginBottom: "2px" }}>Weaknesses</div>
                       <div style={{ fontSize: "12px", color: "#B8B8B8" }}>{feedback.weaknesses}</div>
                     </div>
                   )}
                   {feedback.overall_feedback && (
                     <div style={{ marginTop: "12px", fontSize: "13px", color: "#B8B8B8" }}>
                       {feedback.overall_feedback}
                     </div>
                   )}
                   {feedback.candidate_facing && feedback.candidate_facing_summary && (
                     <div style={{
                       marginTop: "12px", background: "rgba(255,215,0,0.04)",
                       border: "1px solid rgba(255,215,0,0.15)", borderRadius: "8px",
                       padding: "10px 12px"
                     }}>
                       <div style={{ fontSize: "11px", color: "#777", marginBottom: "4px" }}>📢 Shared with Candidate</div>
                       <div style={{ fontSize: "13px", color: "#D4AF37" }}>{feedback.candidate_facing_summary}</div>
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
  const [selectedApps, setSelectedApps] = useState([]);
  const [bulkAction, setBulkAction] = useState("");

  const [selectedApp, setSelectedApp] = useState(null);
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [interviewModalOpen, setInterviewModalOpen] = useState(false);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [messageModalOpen, setMessageModalOpen] = useState(false);
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

  const toggleShortlist = async (app) => {
    const old = app.is_shortlisted;
    try {
      await api.patch(`/api/hr/applications/${app.id}/shortlist`, {}, { skipErrorHandler: true });
      setApplications(apps => apps.map(a => a.id === app.id ? { ...a, is_shortlisted: !old } : a));
      toast.success(`Shortlist ${!old ? "added" : "removed"}`);
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to update shortlist");
    }
  };

  const handleBulkAction = async (action) => {
    if (selectedApps.length === 0) {
      toast.error("Select at least one application");
      return;
    }
    try {
      const payload = { application_ids: selectedApps, action };
      if (action === "bulk_status_update") {
        const status = prompt("Enter new status (APPLIED, UNDER_REVIEW, PHONE_CALL, INTERVIEW, OFFER, REJECTED):");
        if (!status) return;
        payload.status = status;
      } else if (action === "shortlist") {
        payload.is_shortlisted = true;
      }

      await api.post("/api/hr/applications/bulk", payload, { skipErrorHandler: true });
      toast.success(`Bulk action '${action}' completed`);
      setSelectedApps([]);
      await fetchHRApplications();
    } catch (err) {
      toast.error(err.response?.data?.error || "Bulk action failed");
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

      {(statusFilter || search || selectedApps.length > 0) && (
        <div style={{
          display: "flex", gap: "12px", alignItems: "center",
          background: "rgba(255,215,0,0.05)", border: "1px solid rgba(255,215,0,0.1)",
          borderRadius: "10px", padding: "12px 16px", marginBottom: "12px"
        }}>
          {selectedApps.length > 0 && (
            <>
              <span style={{ fontSize: "12px", color: "#B8B8B8" }}>{selectedApps.length} selected</span>
              <select
                className="input-gold"
                style={{ padding: "4px 8px", fontSize: "12px", maxWidth: "180px" }}
                value={bulkAction}
                onChange={(e) => setBulkAction(e.target.value)}
              >
                <option value="">Choose bulk action...</option>
                <option value="shortlist_and_notify">Shortlist (notify)</option>
                <option value="shortlist">Shortlist (silent)</option>
                <option value="bulk_status_update">Bulk Status Update</option>
                <option value="delete" style={{ color: "#ef4444" }}>Delete</option>
              </select>
              <button
                className="btn-gold"
                style={{ padding: "6px 12px", fontSize: "12px" }}
                onClick={() => {
                  if (!bulkAction) return;
                  if (bulkAction === "delete") {
                    if (!confirm(`Delete ${selectedApps.length} applications?`)) return;
                  }
                  handleBulkAction(bulkAction);
                  setBulkAction("");
                }}
              >
                Apply
              </button>
              <button
                className="btn-outline-gold"
                style={{ padding: "6px 12px", fontSize: "12px" }}
                onClick={() => setSelectedApps([])}
              >
                Clear Selection
              </button>
            </>
          )}
          {(statusFilter || search) && selectedApps.length === 0 && (
            <button
              className="btn-outline-gold"
              style={{ padding: "8px 14px", fontSize: "13px", alignSelf: "flex-end" }}
              onClick={() => { setStatusFilter(""); setSearch(""); }}
            >
              ✕ Clear Filters
            </button>
          )}
        </div>
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
                  <th style={{ width: "40px" }}>
                    <input
                      type="checkbox"
                      style={{ accentColor: "#D4AF37" }}
                      checked={applications.length > 0 && selectedApps.length === applications.filter(a => a.candidate?.is_active).length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedApps(applications.filter(a => a.candidate?.is_active).map(a => a.id));
                        } else {
                          setSelectedApps([]);
                        }
                      }}
                    />
                  </th>
                  <th>Candidate</th>
                  <th>Company</th>
                  <th>Job Role</th>
                  <th>Status</th>
                  <th>Shortlist</th>
                  <th>Applied Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((app) => (
                  <tr key={app.id}>
                    <td style={{ width: "40px" }}>
                      <input
                        type="checkbox"
                        style={{ accentColor: "#D4AF37" }}
                        checked={selectedApps.includes(app.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedApps([...new Set([...selectedApps, app.id])]);
                          } else {
                            setSelectedApps(selectedApps.filter(id => id !== app.id));
                          }
                        }}
                      />
                    </td>
                    <td>
                      <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                        <div style={{ fontWeight: 600, color: "#fff", fontSize: "14px" }}>{app.candidate?.name || "Candidate"}</div>
                        <div style={{ fontSize: "11px", color: "#777" }}>{app.candidate?.email}</div>
                        {app.candidate?.phone_number && (
                          <div style={{ fontSize: "10px", color: "#777" }}>{app.candidate.phone_number}</div>
                        )}
                      </div>
                    </td>
                    <td>{app.company}</td>
                    <td>{app.role}</td>
                    <td><StatusBadge status={app.status} /></td>
                    <td>
                      {app.status === "WITHDRAWN" ? null : (
                        // A closed application is never shortlisted, so the
                        // column is left completely empty for it.
                        <button
                          style={{
                            padding: "3px 8px", fontSize: "10px", fontWeight: 600,
                            background: app.is_shortlisted ? "rgba(255,215,0,0.15)" : "rgba(255,255,255,0.04)",
                            border: app.is_shortlisted ? "1px solid rgba(255,215,0,0.4)" : "1px solid #2A2A2A",
                            borderRadius: "4px", color: app.is_shortlisted ? "#FFD700" : "#777",
                            cursor: app.candidate?.is_active ? "pointer" : "not-allowed",
                            opacity: app.candidate?.is_active ? 1 : 0.5
                          }}
                          onClick={() => toggleShortlist(app)}
                          disabled={!app.candidate?.is_active}
                          title={app.is_shortlisted ? "Remove from shortlist" : "Add to shortlist"}
                        >
                          {app.is_shortlisted ? "⭐ Shortlisted" : "☆ Shortlist"}
                        </button>
                      )}
                    </td>
                    <td style={{ fontSize: "12px" }}>
                      {app.applied_date ? new Date(app.applied_date).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—"}
                    </td>
                    <td>
                      {app.status === "WITHDRAWN" ? (
                        // A withdrawn application is closed, so no workflow
                        // actions are available — but it must still be
                        // inspectable through a read-only View.
                        <button
                          style={{
                            padding: "5px 10px", fontSize: "11px", fontWeight: 600,
                            background: "rgba(255,255,255,0.04)", border: "1px solid #2A2A2A",
                            borderRadius: "6px", color: "#B8B8B8", cursor: "pointer",
                          }}
                          onClick={() => fetchDetail(app.id)}
                          title="View this withdrawn application (read only)"
                        >
                          View
                        </button>
                      ) : (
                      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                        <button
                          style={{
                            padding: "5px 10px", fontSize: "11px", fontWeight: 600,
                            background: "rgba(255,215,0,0.08)", border: "1px solid rgba(255,215,0,0.2)",
                            borderRadius: "6px", color: "#D4AF37", cursor: app.candidate?.is_active ? "pointer" : "not-allowed",
                            transition: "all 0.2s", opacity: app.candidate?.is_active ? 1 : 0.5
                          }}
                          onClick={() => { if (app.candidate?.is_active) { setSelectedApp(app); setStatusModalOpen(true); } }}
                          disabled={!app.candidate?.is_active}
                        >
                          Status
                        </button>
                        <button
                          style={{
                            padding: "5px 10px", fontSize: "11px", fontWeight: 600,
                            background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.2)",
                            borderRadius: "6px", color: "#22c55e", cursor: app.candidate?.is_active ? "pointer" : "not-allowed",
                            opacity: app.candidate?.is_active ? 1 : 0.5
                          }}
                          onClick={() => { if (app.candidate?.is_active) { setSelectedApp(app); setInterviewModalOpen(true); } }}
                          disabled={!app.candidate?.is_active}
                        >
                          Interview
                        </button>
                          <button
                            style={{
                              padding: "5px 10px", fontSize: "11px", fontWeight: 600,
                              background: "rgba(139,92,246,0.08)", border: "1px solid rgba(139,92,246,0.2)",
                              borderRadius: "6px", color: "#a78bfa", cursor: app.candidate?.is_active ? "pointer" : "not-allowed",
                              opacity: app.candidate?.is_active ? 1 : 0.5
                            }}
                            onClick={() => { if (app.candidate?.is_active) { setSelectedApp(app); setFeedbackModalOpen(true); } }}
                            disabled={!app.candidate?.is_active}
                          >
                            Feedback
                          </button>
                          <button
                            style={{
                              padding: "5px 10px", fontSize: "11px", fontWeight: 600,
                              background: "rgba(59,130,246,0.08)", border: "1px solid rgba(59,130,246,0.2)",
                              borderRadius: "6px", color: "#60a5fa", cursor: app.candidate?.is_active ? "pointer" : "not-allowed",
                              opacity: app.candidate?.is_active ? 1 : 0.5
                            }}
                            onClick={() => { if (app.candidate?.is_active) { setSelectedApp(app); setMessageModalOpen(true); } }}
                            disabled={!app.candidate?.is_active}
                          >
                            Message
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
                      )}
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

      {messageModalOpen && selectedApp && (
        <MessageModal
          app={selectedApp}
          onClose={() => setMessageModalOpen(false)}
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
