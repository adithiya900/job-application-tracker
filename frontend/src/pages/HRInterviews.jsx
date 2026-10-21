import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
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

export default function HRInterviews() {
  const { user } = useAuth();
  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchInterviews = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (searchQuery) params.set("search", searchQuery);
      const response = await api.get(`/api/hr/interviews?${params}`);
      setInterviews(response.data.applications);
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to load interviews");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInterviews();
  }, [statusFilter, searchQuery]);

  if (!user || user.role !== "HR") {
    return null;
  }

  const filteredInterviews = interviews.filter((app) => {
    const statusMatch =
      !statusFilter || app.interview_details.some(
        (i) => i.round_type === statusFilter
      );
    const searchMatch =
      !searchQuery ||
      app.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (app.candidate_name || "").toLowerCase().includes(searchQuery.toLowerCase());
    return statusMatch && searchMatch;
  });

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>HR Interview Management</h1>
        <p>Manage all interview schedules across applications</p>
      </div>

      <div className="controls-bar">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search company, role, or candidate..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-gold"
            placeholder="Search company, role, candidate..."
          />
        </div>
        <div className="filter-row">
          <label className="label-gold">Filter by Round Type:</label>
          <select
            className="input-gold"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Rounds</option>
            <option value="Phone Screen">Phone Screen</option>
            <option value="Technical Round 1">Technical Round 1</option>
            <option value="Technical Round 2">Technical Round 2</option>
            <option value="HR Round">HR Round</option>
            <option value="Managerial Round">Managerial Round</option>
            <option value="Final Round">Final Round</option>
            <option value="Custom">Custom</option>
          </select>
        </div>
        <button
          className="btn-primary"
          onClick={() => {
            setSearchQuery("");
            setStatusFilter("");
          }}
        >
          Clear Filters
        </button>
      </div>

      <div className="interviews-table-container">
        <table className="premium-table">
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Company</th>
              <th>Role</th>
              <th>Status</th>
              <th>Round</th>
              <th>Round Type</th>
              <th>Interview Type</th>
              <th>Date</th>
              <th>Time</th>
              <th>Interviewer</th>
              <th>Meeting Link</th>
              <th>Last Updated</th>
            </tr>
          </thead>
          <tbody>
            {filteredInterviews.length === 0 ? (
              <tr>
                <td colSpan="12" style={{ textAlign: "center", color: "#888" }}>
                  No interview records found matching your criteria.
                </td>
              </tr>
            ) : (
              filteredInterviews.map((app) => {
                const details = app.interview_details || [];
                return (
                  <tr key={app.id}>
                    <td>
                      <div style={{ fontWeight: 600, color: "#fff" }}>
                        {app.candidate_name || "Unknown Candidate"}
                      </div>
                      <div style={{ fontSize: "12px", color: "#B8B8B8" }}>
                        {app.candidate_email || "—"}
                      </div>
                    </td>
                    <td>{app.company}</td>
                    <td>{app.role}</td>
                    <td><StatusBadge status={app.status} /></td>
                    <td>{details.length > 0 ? details.map(d => d.interview_round).join(", ") : "—"}</td>
                    <td>{details.length > 0 ? details.map(d => d.round_type).join(", ") : "—"}</td>
                    <td>{details.length > 0 ? details.map(d => d.interview_type).join(", ") : "—"}</td>
                    <td>{details.length > 0 ? formatDate(details[0].interview_date) : "—"}</td>
                    <td>{details.length > 0 ? formatTime(details[0].interview_time) : "—"}</td>
                    <td>{details.length > 0 ? details.map(d => d.interviewer).join(", ") : "—"}</td>
                    <td>
                      {details.length > 0 && details.map(d => d.meeting_link).filter(Boolean).length > 0 ? (
                        <a href={details.map(d => d.meeting_link).find(Boolean)} target="_blank" rel="noopener noreferrer" style={{ color: "#D4AF37", textDecoration: "underline" }}>
                          View Link
                        </a>
                      ) : "—"}
                    </td>
                    <td>{details.length > 0 ? new Date(details[0].created_at).toLocaleDateString() : "—"}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}