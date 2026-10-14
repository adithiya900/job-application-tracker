import { useState, useEffect, useCallback } from "react";
import api from "../services/api";
import toast from "react-hot-toast";
import { STATUS_CONFIG } from "../components/StatusBadge";

const REPORT_TYPES = [
  { value: "overview", label: "Overview" },
  { value: "applications", label: "Applications Report" },
  { value: "users", label: "Users Report" },
  { value: "feedback", label: "Feedback Report" },
];

function SkeletonBar({ width = "100%", height = "20px" }) {
  return <div className="skeleton" style={{ width, height, borderRadius: "6px" }} />;
}

export default function AdminReports() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reportType, setReportType] = useState("overview");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const fetchReport = useCallback(async () => {
    if (!reportType) return;

    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.set("type", reportType);
      if (dateFrom) params.set("from", dateFrom);
      if (dateTo) params.set("to", dateTo);

      const res = await api.get(`/api/admin/reports?${params}`, { skipErrorHandler: true });
      setReport(res.data);
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to load report");
    } finally {
      setLoading(false);
    }
  }, [reportType, dateFrom, dateTo]);

  useEffect(() => {
    document.title = "Admin Reports — Job Tracker";
    fetchReport();
  }, [fetchReport]);

  const STATUS_COLORS = {
    "APPLIED": "#D4AF37",
    "UNDER_REVIEW": "#F5C542",
    "PHONE_CALL": "#E8B84B",
    "INTERVIEW": "#FFD700",
    "OFFER": "#22c55e",
    "REJECTED": "#ef4444",
    "WITHDRAWN": "#6b7280",
  };

  const renderOverview = () => {
    if (loading) {
      return <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {[...Array(6)].map((_, i) => <SkeletonBar key={i} height="40px" />)}
      </div>;
    }

    const summary = report?.summary || {};
    const statusItems = Object.entries(report?.applications_by_status || {});
    const roleItems = Object.entries(report?.users_by_role || {});

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {/* Summary Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "14px" }}>
          {[
            { label: "Total Users", value: summary.total_users, color: "#60a5fa", icon: "👥" },
            { label: "Total Applications", value: summary.total_applications, color: "#FFD700", icon: "📊" },
            { label: "Total Interviews", value: summary.total_interviews, color: "#a78bfa", icon: "🎙" },
            { label: "Total Feedback", value: summary.total_feedback, color: "#22c55e", icon: "📝" },
            { label: "Shortlisted", value: summary.total_shortlisted, color: "#D4AF37", icon: "🎯" },
            { label: "Active Users", value: summary.active_users, color: "#22c55e", icon: "✉️" },
          ].map((item) => (
            <div key={item.label} className="stat-card">
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
                <span style={{ fontSize: "20px" }}>{item.icon}</span>
              </div>
              <div style={{ fontSize: "32px", fontWeight: 800, color: item.color, lineHeight: 1 }}>
                {item.value ?? 0}
              </div>
              <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>{item.label}</div>
            </div>
          ))}
        </div>

        {/* Status and Role Breakdown */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
          <div style={{ background: "#111111", border: "1px solid #1F1F1F", borderRadius: "12px", padding: "20px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>Applications by Status</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {statusItems.map(([status, count]) => (
                <div key={status} style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "12px" }}>
                  <div style={{ width: "12px", height: "12px", borderRadius: "3px", background: STATUS_COLORS[status] || "#555" }} />
                  <span style={{ color: "#B8B8B8", width: "120px" }}>{STATUS_CONFIG[status]?.label || status}</span>
                  <span style={{ color: "#fff", fontWeight: 600 }}>{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: "#111111", border: "1px solid #1F1F1F", borderRadius: "12px", padding: "20px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>Users by Role</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {roleItems.map(([role, count]) => (
                <div key={role} style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "12px" }}>
                  <div style={{ width: "12px", height: "12px", borderRadius: "50%", background: "#D4AF37" }} />
                  <span style={{ color: "#B8B8B8", width: "120px", textTransform: "capitalize" }}>{role.toLowerCase()}</span>
                  <span style={{ color: "#fff", fontWeight: 600 }}>{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderApplicationsReport = () => {
    if (loading) {
      return <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {[...Array(6)].map((_, i) => <SkeletonBar key={i} height="40px" />)}
      </div>;
    }

    const data = report;

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "14px" }}>
          <div className="stat-card">
            <div style={{ fontSize: "32px", fontWeight: 800, color: "#FFD700" }}>{data?.total_applications || 0}</div>
            <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>Total Applications</div>
          </div>
        </div>

        {/* Status Breakdown */}
        <div style={{ background: "#111111", border: "1px solid #1F1F1F", borderRadius: "12px", padding: "20px" }}>
          <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>By Status</h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "16px" }}>
            {Object.entries(data?.by_status || {}).map(([status, count]) => (
              <div key={status} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
                <div style={{
                  width: "50px", height: "50px", borderRadius: "50%",
                  background: STATUS_COLORS[status] || "#555",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "11px", fontWeight: 700, color: "#fff"
                }}>{count}</div>
                <span style={{ fontSize: "11px", color: "#777", textTransform: "capitalize" }}>
                  {STATUS_CONFIG[status]?.label || status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Companies */}
        {data?.top_companies && data.top_companies.length > 0 && (
          <div style={{ background: "#111111", border: "1px solid #1F1F1F", borderRadius: "12px", padding: "20px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>Top Companies</h3>
            <table className="premium-table">
              <thead>
                <tr><th>#</th><th>Company</th><th>Applications</th></tr>
              </thead>
              <tbody>
                {data.top_companies.map((c, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td>{c.company}</td>
                    <td>{c.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Daily Trend */}
        {data?.daily_trend && data.daily_trend.length > 0 && (
          <div style={{ background: "#111111", border: "1px solid #1F1F1F", borderRadius: "12px", padding: "20px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>Daily Trend</h3>
            <table className="premium-table">
              <thead>
                <tr><th>Date</th><th>Applications</th></tr>
              </thead>
              <tbody>
                {data.daily_trend.map((d) => (
                  <tr key={d.date}>
                    <td>{d.date}</td>
                    <td>{d.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  const renderUsersReport = () => {
    if (loading) {
      return <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {[...Array(6)].map((_, i) => <SkeletonBar key={i} height="40px" />)}
      </div>;
    }

    const data = report;
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "14px" }}>
          <div className="stat-card">
            <div style={{ fontSize: "32px", fontWeight: 800, color: "#60a5fa" }}>{data?.total_users || 0}</div>
            <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>Total Users</div>
          </div>
          <div className="stat-card">
            <div style={{ fontSize: "32px", fontWeight: 800, color: "#22c55e" }}>{data?.active_users || 0}</div>
            <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>Active</div>
          </div>
        </div>

        <div style={{ background: "#111111", border: "1px solid #1F1F1F", borderRadius: "12px", padding: "20px" }}>
          <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>By Role</h3>
          <table className="premium-table">
            <thead>
              <tr><th>Role</th><th>Count</th></tr>
            </thead>
            <tbody>
              {Object.entries(data?.by_role || {}).map(([role, count]) => (
                <tr key={role}>
                  <td>{role.toLowerCase()}</td>
                  <td>{count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {data?.weekly_growth && data.weekly_growth.length > 0 && (
          <div style={{ background: "#111111", border: "1px solid #1F1F1F", borderRadius: "12px", padding: "20px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>Weekly Growth</h3>
            <table className="premium-table">
              <thead>
                <tr><th>Date</th><th>New Users</th></tr>
              </thead>
              <tbody>
                {data.weekly_growth.map((d) => (
                  <tr key={d.date}>
                    <td>{d.date}</td>
                    <td>{d.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  const renderFeedbackReport = () => {
    if (loading) {
      return <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {[...Array(4)].map((_, i) => <SkeletonBar key={i} height="40px" />)}
      </div>;
    }

    const data = report;
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "14px" }}>
          <div className="stat-card">
            <div style={{ fontSize: "32px", fontWeight: 800, color: "#22c55e" }}>{data?.total_feedback || 0}</div>
            <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>Total Feedback</div>
          </div>
          <div className="stat-card">
            <div style={{ fontSize: "32px", fontWeight: 800, color: "#FFD700" }}>{data?.shortlisted_count || 0}</div>
            <div style={{ fontSize: "11px", color: "#777", marginTop: "6px", fontWeight: 500 }}>Shortlisted</div>
          </div>
        </div>

        {data?.by_recommendation && data.by_recommendation.length > 0 && (
          <div style={{ background: "#111111", border: "1px solid #1F1F1F", borderRadius: "12px", padding: "20px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#fff", marginBottom: "16px" }}>By Recommendation</h3>
            <table className="premium-table">
              <thead>
                <tr><th>Recommendation</th><th>Count</th><th>Avg Rating</th></tr>
              </thead>
              <tbody>
                {data.by_recommendation.map((item, i) => {
                  const color = item.recommendation === "Hire" ? "#22c55e" : item.recommendation === "Maybe" ? "#FFD700" : "#ef4444";
                  return (
                    <tr key={i}>
                      <td style={{ color: color, fontWeight: 600 }}>{item.recommendation || "N/A"}</td>
                      <td>{item.count}</td>
                      <td>{item.average_rating !== null ? item.average_rating : "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#fff", marginBottom: "6px" }}>
          Reports 📈
        </h1>
        <p style={{ color: "#777", fontSize: "14px" }}>
          Generate and view detailed reports across your application pipeline.
        </p>
      </div>

      {/* Controls */}
      <div style={{
        background: "#111111", border: "1px solid #1F1F1F",
        borderRadius: "12px", padding: "16px 20px",
        display: "flex", gap: "14px", flexWrap: "wrap", alignItems: "flex-end"
      }}>
        <div style={{ flex: "1 1 160px", minWidth: "140px" }}>
          <label className="label-gold">Report Type</label>
          <select className="input-gold" value={reportType} onChange={(e) => setReportType(e.target.value)}>
            {REPORT_TYPES.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>

        <div style={{ flex: "1 1 140px", minWidth: "130px" }}>
          <label className="label-gold">From (YYYY-MM-DD)</label>
          <input
            type="date"
            className="input-gold"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>

        <div style={{ flex: "1 1 140px", minWidth: "130px" }}>
          <label className="label-gold">To (YYYY-MM-DD)</label>
          <input
            type="date"
            className="input-gold"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>

        <div style={{ flex: "1 1 100px" }}>
          <button
            className="btn-gold"
            style={{ padding: "10px 16px" }}
            onClick={() => fetchReport()}
          >
            Generate
          </button>
        </div>
      </div>

      {/* Report Content */}
      {report && (
        <div style={{
          background: "#111111", border: "1px solid #1F1F1F",
          borderRadius: "12px", padding: "20px"
        }}>
          <div style={{ fontSize: "11px", color: "#777", marginBottom: "12px", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Report period: {report.period?.from} to {report.period?.to} · Type: {report.report_type}
          </div>
          {reportType === "overview" && renderOverview()}
          {reportType === "applications" && renderApplicationsReport()}
          {reportType === "users" && renderUsersReport()}
          {reportType === "feedback" && renderFeedbackReport()}
        </div>
      )}
    </div>
  );
}
