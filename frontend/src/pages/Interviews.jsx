import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useNotifications } from "../contexts/NotificationContext";
import api from "../services/api";
import toast from "react-hot-toast";

const STATUS_COLORS = {
  APPLIED: "#D4AF37",
  UNDER_REVIEW: "#E8B84B",
  PHONE_CALL: "#FFD700",
  INTERVIEW: "#FFD700",
  OFFER: "#22c55e",
  REJECTED: "#ef4444",
  WITHDRAWN: "#6b7280",
};

function formatDate(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatTime(timeStr) {
  if (!timeStr) return "—";
  return timeStr;
}

export default function Interviews() {
  const { user } = useAuth();
  const { notifications } = useNotifications();
  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchInterviews = async () => {
    setLoading(true);
    try {
      const response = await api.get("/api/applications", {
        skipErrorHandler: true,
      });
      const allApplications = response.data.applications || [];
      const interviews = allApplications.filter((app) => {
        return app.interview_details && app.interview_details.length > 0;
      });
      setInterviews(interviews);
    } catch (err) {
      console.error("Failed to fetch applications:", err);
      toast.error("Failed to load interview applications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInterviews();
  }, []);

  if (!user) return null;

  const interviewsByApp = interviews.map((app) => {
    const latestDetail =
      app.interview_details && app.interview_details.length > 0
        ? app.interview_details[app.interview_details.length - 1]
        : null;
    return {
      ...app,
      latestInterview: latestDetail,
    };
  });

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>My Interviews</h1>
        <p>View your scheduled interviews and their details</p>
      </div>

      <div className="interviews-container">
        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "300px" }}>
            <div className="spinner-gold" style={{ width: 40, height: 40 }} />
          </div>
        ) : interviewsByApp.length === 0 ? (
          <div className="empty-state">
            <div style={{ fontSize: "48px", marginBottom: "16px" }}>📅</div>
            <h3>No Interviews Scheduled</h3>
            <p>You don't have any upcoming interviews. Once an HR representative schedules an interview for you, it will appear here.</p>
          </div>
        ) : (
          <div className="interviews-list">
            {interviewsByApp.map((app) => {
              const detail = app.latestInterview;
              return (
                <div key={app.id} className="interview-card">
                  <div className="interview-header">
                    <div className="company-info">
                      <div style={{ fontWeight: 600, color: "#fff" }}>{app.company}</div>
                      <div style={{ color: "#B8B8B8", fontSize: "14px" }}>{app.role}</div>
                    </div>
                    <div className="status-badge">
                      <StatusBadge status={app.status} />
                    </div>
                  </div>
                  <div className="interview-details">
                    <div className="detail-row">
                      <span className="label">Round:</span>
                      <span>{detail?.round_type || detail?.interview_round || "N/A"}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Type:</span>
                      <span>{detail?.interview_type || "—"}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Date:</span>
                      <span>{detail?.interview_date ? formatDate(detail.interview_date) : "—"}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Time:</span>
                      <span>{detail?.interview_time || "—"}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Interviewer:</span>
                      <span>{detail?.interviewer || "—"}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Meeting Link:</span>
                      <span style={{ color: "#D4AF37" }}>
                        {detail?.meeting_link ? (
                          <a href={detail.meeting_link} target="_blank" rel="noopener noreferrer">
                            Join Interview
                          </a>
                        ) : "—"}
                      </span>
                    </div>
                  </div>
                  <div className="interview-actions">
                    <button
                      className="btn-primary"
                      onClick={() => window.open(detail.meeting_link, "_blank")}
                      disabled={!detail?.meeting_link}
                    >
                      Join Interview
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const STATUS_COLORS = {
    APPLIED: "#D4AF37",
    UNDER_REVIEW: "#E8B84B",
    PHONE_CALL: "#FFD700",
    INTERVIEW: "#FFD700",
    OFFER: "#22c55e",
    REJECTED: "#ef4444",
    WITHDRAWN: "#6b7280",
  };
  return (
    <span
      style={{
        padding: "4px 12px",
        borderRadius: "12px",
        background: STATUS_COLORS[status] || "#D4AF37",
        color: "#000",
        fontSize: "11px",
        fontWeight: 700,
        textTransform: "uppercase",
      }}
    >
      {status.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
    </span>
  );
}