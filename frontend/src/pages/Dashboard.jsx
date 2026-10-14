import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import StatusBadge from "../components/StatusBadge";
import useApplicationStore from "../stores/applicationStore";
import { useNotifications } from "../contexts/NotificationContext";

const STAT_CARDS = [
  { key: "total_applications", label: "Total", icon: "📊", accent: "#FFD700" },
  { key: "APPLIED",            label: "Applied",       icon: "📝", accent: "#D4AF37" },
  { key: "UNDER_REVIEW",       label: "Under Review",  icon: "🔍", accent: "#F5C542" },
  { key: "PHONE_CALL",       label: "Phone Call",  icon: "📞", accent: "#E8B84B" },
  { key: "INTERVIEW",          label: "Interview",     icon: "🎙", accent: "#FFD700" },
  { key: "OFFER",              label: "Offers",        icon: "🎉", accent: "#22c55e" },
  { key: "REJECTED",           label: "Rejected",      icon: "❌", accent: "#ef4444" },
  { key: "WITHDRAWN",          label: "Withdrawn",     icon: "↩", accent: "#6b7280" },
];

function Skeleton({ width = "100%", height = "20px" }) {
  return (
    <div className="skeleton" style={{ width, height, borderRadius: "6px" }} />
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { notifications } = useNotifications();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const applications = useApplicationStore((s) => s.applications);
  const fetchApplications = useApplicationStore((s) => s.fetchApplications);

  useEffect(() => {
    document.title = "Dashboard — Job Tracker";

    const fetchData = async () => {
      try {
        setLoading(true);
        const [analyticsRes] = await Promise.all([
          api.get("/api/analytics", { skipErrorHandler: true }),
          fetchApplications(),
        ]);
        setAnalytics(analyticsRes.data);
      } catch (err) {
        setError(err.response?.data?.message || "Failed to load dashboard data.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (notifications.length === 0) return undefined;

    let cancelled = false;

    api.get("/api/analytics", { skipErrorHandler: true })
      .then((response) => {
        if (!cancelled) setAnalytics(response.data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.response?.data?.message || "Failed to refresh dashboard statistics.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [notifications.length]);

  const byStatus = analytics?.by_status || {};
  const total = analytics?.total_applications ?? 0;

  const getStatValue = (key) => {
    if (key === "total_applications") return total;
    return byStatus[key] ?? 0;
  };

  const recentApps = applications.slice(0, 5);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#FFD700", marginBottom: "6px" }}>
          Hello, {user?.name?.split(" ")[0] || "there"} 👋
        </h1>
        <p style={{ color: "#A88A2A", fontSize: "14px" }}>
          Here's your job search overview for today.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)",
          borderRadius: "10px", padding: "14px 16px", color: "#ef4444", fontSize: "13px"
        }}>
          ⚠ {error}
        </div>
      )}

      {/* Stats Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
        gap: "14px"
      }}>
        {STAT_CARDS.map((card) => (
          <div key={card.key} className="stat-card">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
              <span style={{ fontSize: "20px" }}>{card.icon}</span>
              {loading && <Skeleton width="40px" height="14px" />}
            </div>
            {loading ? (
              <Skeleton width="60px" height="32px" />
            ) : (
              <div style={{
                fontSize: "32px", fontWeight: 800,
                color: card.accent, lineHeight: 1
              }}>
                {getStatValue(card.key)}
              </div>
            )}
            <div style={{ fontSize: "12px", color: "#A88A2A", marginTop: "6px", fontWeight: 500 }}>
              {card.label}
            </div>
          </div>
        ))}
      </div>

      {/* Recent Applications */}
      <div>
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          marginBottom: "16px"
        }}>
          <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#FFD700" }}>
            Recent Applications
          </h2>
          <Link to="/applications" style={{
            color: "#D4AF37", fontSize: "13px", fontWeight: 500,
            textDecoration: "none",
            display: "flex", alignItems: "center", gap: "4px"
          }}>
            View all →
          </Link>
        </div>

        <div style={{
          background: "#111111", border: "1px solid #1F1F1F",
          borderRadius: "12px", overflow: "hidden"
        }}>
          {loading ? (
            <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
              {[1,2,3].map(i => (
                <div key={i} style={{ display: "flex", gap: "16px", alignItems: "center" }}>
                  <Skeleton width="120px" height="16px" />
                  <Skeleton width="180px" height="16px" />
                  <Skeleton width="80px" height="22px" />
                </div>
              ))}
            </div>
          ) : recentApps.length === 0 ? (
            <div style={{
              padding: "60px 24px", textAlign: "center"
            }}>
              <div style={{ fontSize: "40px", marginBottom: "12px" }}>🗂️</div>
              <div style={{ fontSize: "16px", fontWeight: 600, color: "#FFD700", marginBottom: "6px" }}>
                No Applications Yet
              </div>
              <p style={{ fontSize: "13px", color: "#A88A2A", marginBottom: "20px" }}>
                Start tracking your job applications today.
              </p>
              <Link to="/applications/add" className="btn-gold" style={{ textDecoration: "none" }}>
                + Add Your First Application
              </Link>
            </div>
          ) : (
            <table className="premium-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Job Role</th>
                  <th>Status</th>
                  <th>Applied Date</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {recentApps.map((app) => (
                  <tr key={app.id}>
                    <td style={{ color: "#FFD700", fontWeight: 600 }}>{app.company}</td>
                    <td>{app.role}</td>
                    <td><StatusBadge status={app.status} /></td>
                    <td>{app.applied_date ? new Date(app.applied_date).toLocaleDateString() : "—"}</td>
                    <td>
                      <button
                        className="btn-outline-gold"
                        style={{ padding: "6px 14px", fontSize: "12px" }}
                        onClick={() => navigate(`/applications?detail=${app.id}`)}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Quick Links */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
        gap: "14px"
      }}>
        {[
          { to: "/applications/add", icon: "➕", title: "Add Application", desc: "Track a new job application" },
          { to: "/jobs", icon: "🔍", title: "Search Jobs", desc: "Find new opportunities" },
          { to: "/applications", icon: "📋", title: "My Applications", desc: "Manage all applications" },
          { to: "/settings", icon: "⚙", title: "Settings", desc: "Update profile & preferences" },
        ].map((link) => (
          <Link
            key={link.to}
            to={link.to}
            style={{ textDecoration: "none" }}
          >
            <div className="premium-card" style={{ padding: "20px" }}>
              <div style={{ fontSize: "24px", marginBottom: "10px" }}>{link.icon}</div>
              <div style={{ fontSize: "14px", fontWeight: 600, color: "#FFD700", marginBottom: "4px" }}>
                {link.title}
              </div>
              <div style={{ fontSize: "12px", color: "#A88A2A" }}>{link.desc}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}