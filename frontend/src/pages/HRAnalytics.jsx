import { useState, useEffect, useCallback } from "react";
import api from "../services/api";
import toast from "react-hot-toast";
import { STATUS_CONFIG } from "../components/StatusBadge";

const STATUS_COLORS = {
  "APPLIED": "#D4AF37",
  "UNDER_REVIEW": "#F5C542",
  "PHONE_CALL": "#E8B84B",
  "INTERVIEW": "#FFD700",
  "OFFER": "#22c55e",
  "REJECTED": "#ef4444",
  "WITHDRAWN": "#6b7280",
};

function SkeletonBar({ width = "100%", height = "20px" }) {
  return <div className="skeleton" style={{ width, height, borderRadius: "6px" }} />;
}

export default function HRAnalytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get("/api/hr/analytics", { skipErrorHandler: true });
      setAnalytics(res.data);
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    document.title = "HR Analytics — Job Tracker";
    fetchAnalytics();
  }, [fetchAnalytics]);

  // Calculate total from status counts
  const totalApplications = analytics?.status_counts
    ? Object.values(analytics.status_counts).reduce((a, b) => a + (b || 0), 0)
    : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#fff", marginBottom: "6px" }}>
          HR Analytics 📊
        </h1>
        <p style={{ color: "#777", fontSize: "14px" }}>
          Insights into your hiring pipeline and candidate performance.
        </p>
      </div>

      {/* Summary Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "14px" }}>
        <div className="stat-card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
            <span style={{ fontSize: "20px" }}>📊</span>
          </div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: "#FFD700", lineHeight: 1 }}>
            {loading ? <SkeletonBar width="40px" height="28px" /> : totalApplications}
          </div>
          <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>Total Applications</div>
        </div>

        <div className="stat-card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
            <span style={{ fontSize: "20px" }}>⭐</span>
          </div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: "#FFD700", lineHeight: 1 }}>
            {loading ? <SkeletonBar width="40px" height="28px" /> : (analytics?.average_rating || "—")}
          </div>
          <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>Avg Rating</div>
        </div>

        <div className="stat-card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
            <span style={{ fontSize: "20px" }}>📝</span>
          </div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: "#22c55e", lineHeight: 1 }}>
            {loading ? <SkeletonBar width="40px" height="28px" /> : (analytics?.feedback_count || 0)}
          </div>
          <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>Total Feedback</div>
        </div>

        <div className="stat-card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
            <span style={{ fontSize: "20px" }}>🎯</span>
          </div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: "#FFD700", lineHeight: 1 }}>
            {loading ? <SkeletonBar width="40px" height="28px" /> : (analytics?.shortlisted_count || 0)}
          </div>
          <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>Shortlisted</div>
        </div>

        <div className="stat-card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
            <span style={{ fontSize: "20px" }}>👥</span>
          </div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: "#60a5fa", lineHeight: 1 }}>
            {loading ? <SkeletonBar width="40px" height="28px" /> : (analytics?.active_candidates || 0)}
          </div>
          <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>Active Candidates</div>
        </div>
      </div>

      {/* Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* Status Distribution */}
        <div style={{
          background: "#111111", border: "1px solid #1F1F1F",
          borderRadius: "12px", padding: "20px"
        }}>
          <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>
            Applications by Status
          </h3>
          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {[...Array(7)].map((_, i) => (
                <SkeletonBar key={i} height="20px" />
              ))}
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {Object.entries(analytics?.status_counts || {}).map(([status, count]) => {
                const percentage = totalApplications > 0 ? (count / totalApplications) * 100 : 0;
                return (
                  <div key={status} style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "12px" }}>
                    <div style={{ width: "14px", height: "14px", borderRadius: "3px",
                      background: STATUS_COLORS[status] || "#555", minWidth: "14px" }} />
                    <span style={{ width: "100px", color: "#B8B8B8", textTransform: "capitalize" }}>
                      {STATUS_CONFIG[status]?.label || status}
                    </span>
                    <div style={{ flex: 1, background: "#0B0B0B", borderRadius: "4px", height: "8px", overflow: "hidden" }}>
                      <div style={{
                        width: `${Math.max(percentage, 2)}%`, height: "100%",
                        background: STATUS_COLORS[status] || "#555",
                        transition: "width 0.5s ease"
                      }} />
                    </div>
                    <span style={{ color: "#fff", fontWeight: 600, minWidth: "30px", textAlign: "right" }}>{count}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Applications Over Time */}
        <div style={{
          background: "#111111", border: "1px solid #1F1F1F",
          borderRadius: "12px", padding: "20px"
        }}>
          <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>
            Applications (Last 30 Days)
          </h3>
          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {[...Array(10)].map((_, i) => (
                <SkeletonBar key={i} height="60px" />
              ))}
            </div>
          ) : analytics?.monthly_trend && analytics.monthly_trend.length > 0 ? (
            <div style={{ display: "flex", alignItems: "flex-end", gap: "4px", height: "160px", padding: "8px 4px" }}>
              {analytics.monthly_trend.map((day) => (
                <div key={day.date} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", height: "100%" }}>
                  <div style={{
                    width: "100%", height: "100%",
                    background: day.count > 0 ? "linear-gradient(180deg, #D4AF37, #FFD700)" : "#0B0B0B",
                    borderRadius: "3px 3px 0 0",
                    minHeight: "4px",
                    display: "flex", alignItems: "flex-end", justifyContent: "center",
                    position: "relative"
                  }}>
                    {day.count > 0 && (
                      <span style={{
                        position: "absolute", top: "-16px", fontSize: "9px",
                        color: "#777", whiteSpace: "nowrap"
                      }}>{day.count}</span>
                    )}
                  </div>
                  <div style={{ fontSize: "8px", color: "#555", marginTop: "2px", transform: "rotate(-45deg)" }}>
                    {new Date(day.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: "13px", color: "#777", textAlign: "center", padding: "20px" }}>
              No applications in the selected period.
            </p>
          )}
        </div>
      </div>

      {/* Top Companies & Top Candidates */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* Top Companies */}
        <div style={{
          background: "#111111", border: "1px solid #1F1F1F",
          borderRadius: "12px", padding: "20px"
        }}>
          <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>
            Top Companies by Applications
          </h3>
          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {[...Array(5)].map((_, i) => (
                <SkeletonBar key={i} height="18px" />
              ))}
            </div>
          ) : analytics?.top_companies && analytics.top_companies.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {analytics.top_companies.map((item, idx) => (
                <div key={idx} style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "12px" }}>
                  <span style={{
                    fontSize: "10px", fontWeight: 700, color: "#777",
                    minWidth: "20px", textAlign: "center"
                  }}>{idx + 1}</span>
                  <span style={{ color: "#B8B8B8", flex: 1 }}>{item.company}</span>
                  <span style={{
                    fontWeight: 700, color: "#FFD700",
                    background: "rgba(212,175,55,0.1)",
                    padding: "2px 8px", borderRadius: "10px", fontSize: "11px"
                  }}>{item.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: "13px", color: "#777" }}>No data available.</p>
          )}
        </div>

        {/* Top Candidates */}
        <div style={{
          background: "#111111", border: "1px solid #1F1F1F",
          borderRadius: "12px", padding: "20px"
        }}>
          <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>
            Most Engaged Candidates
          </h3>
          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {[...Array(5)].map((_, i) => (
                <SkeletonBar key={i} height="18px" />
              ))}
            </div>
          ) : analytics?.top_candidates && analytics.top_candidates.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {analytics.top_candidates.map((item, idx) => (
                <div key={idx} style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "12px" }}>
                  <span style={{
                    fontSize: "10px", fontWeight: 700, color: "#777",
                    minWidth: "20px", textAlign: "center"
                  }}>{idx + 1}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ color: "#fff", fontWeight: 500 }}>{item.name}</div>
                    <div style={{ color: "#777", fontSize: "10px" }}>{item.email}</div>
                  </div>
                  <span style={{
                    fontWeight: 700, color: "#60a5fa",
                    background: "rgba(96,165,250,0.1)",
                    padding: "2px 8px", borderRadius: "10px", fontSize: "11px"
                  }}>{item.count} apps</span>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: "13px", color: "#777" }}>No data available.</p>
          )}
        </div>
      </div>

      {/* Feedback Recommendations Breakdown */}
      {analytics && (
        <div style={{
          background: "#111111", border: "1px solid #1F1F1F",
          borderRadius: "12px", padding: "20px"
        }}>
          <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>
            Feedback Recommendations Breakdown
          </h3>
          <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
            {["Hire", "Maybe", "No Hire"].map((rec) => {
              const count = analytics.recommendation_counts?.[rec] || 0;
              const color = rec === "Hire" ? "#22c55e" : rec === "Maybe" ? "#FFD700" : "#ef4444";
              return (
                <div key={rec} style={{
                  flex: "1", minWidth: "120px",
                  background: "rgba(255,255,255,0.02)",
                  border: `1px solid ${color}20`, borderRadius: "10px", padding: "16px"
                }}>
                  <div style={{ fontSize: "12px", color: "#777", marginBottom: "8px" }}>{rec}</div>
                  <div style={{ fontSize: "20px", fontWeight: 700, color: color }}>{count}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
