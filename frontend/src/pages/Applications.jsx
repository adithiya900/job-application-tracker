import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { useDropzone } from "react-dropzone";
import axios from "axios";
import toast from "react-hot-toast";
import useApplicationStore from "../stores/applicationStore";
import api from "../services/api";
import StatusBadge, { STATUS_CONFIG } from "../components/StatusBadge";

// ─── Resume Upload Cell ──────────────────────────────────────────────────────

function ResumeCell({ application }) {
  const fetchApplications = useApplicationStore((s) => s.fetchApplications);
  const [resumeFile, setResumeFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [resumeExists, setResumeExists] = useState(Boolean(application.resume_path));

  useEffect(() => {
    setResumeExists(Boolean(application.resume_path));
    if (!application.resume_path) { setResumeFile(null); setUploadProgress(0); }
  }, [application.resume_path]);

  const uploadResume = async (file) => {
    if (!file) return;
    setError(""); setUploading(true); setUploadProgress(0);
    const fd = new FormData();
    fd.append("resume", file);
    try {
      await api.post(`/api/applications/${application.id}/resume`, fd, {
        skipErrorHandler: true,
        onUploadProgress: (e) => {
          if (e.total) setUploadProgress(Math.round((e.loaded * 100) / e.total));
        },
      });
      setResumeFile(file); setResumeExists(true); setUploadProgress(100);
      toast.success("Resume uploaded!");
      await fetchApplications();
    } catch (err) {
      setError(err.response?.data?.error || "Upload failed.");
      toast.error("Resume upload failed."); setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const deleteResume = async () => {
    if (!window.confirm("Delete this resume?")) return;
    setError("");
    try {
      await api.delete(`/api/applications/${application.id}/resume`, {
        skipErrorHandler: true,
      });
      setResumeFile(null); setResumeExists(false); setUploadProgress(0);
      toast.success("Resume deleted.");
      await fetchApplications();
    } catch (err) {
      setError(err.response?.data?.error || "Delete failed.");
      toast.error("Resume delete failed.");
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { "application/pdf": [".pdf"] },
    multiple: false, disabled: uploading,
    onDropRejected: () => toast.error("Only PDF files are allowed."),
    onDrop: (files) => { setError(""); if (files[0]) uploadResume(files[0]); },
  });

  const filename = resumeFile?.name || (application.resume_path ? application.resume_path.split(/[\\/]/).pop() : "");

  return (
    <div style={{ minWidth: "180px" }}>
      {!resumeExists && !uploading && (
        <div {...getRootProps()} style={{
          border: `2px dashed ${isDragActive ? "#FFD700" : "#2A2A2A"}`,
          borderRadius: "8px", padding: "12px 8px", textAlign: "center",
          cursor: "pointer", transition: "all 0.2s",
          background: isDragActive ? "rgba(255,215,0,0.06)" : "transparent"
        }}>
          <input {...getInputProps()} />
          <div style={{ fontSize: "11px", color: "#777" }}>
            {isDragActive ? "Drop PDF" : "📎 Upload PDF"}
          </div>
        </div>
      )}

      {uploading && (
        <div style={{ padding: "8px 0" }}>
          <div style={{ fontSize: "11px", color: "#B8B8B8", marginBottom: "6px" }}>
            Uploading... {uploadProgress}%
          </div>
          <div style={{ height: "4px", background: "#1F1F1F", borderRadius: "2px" }}>
            <div style={{ width: `${uploadProgress}%`, height: "100%", background: "#FFD700", borderRadius: "2px", transition: "width 0.3s" }} />
          </div>
        </div>
      )}

      {resumeExists && !uploading && (
        <div>
          <div style={{
            fontSize: "11px", color: "#D4AF37", marginBottom: "6px",
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap"
          }}>
            📄 {filename || "Resume uploaded"}
          </div>
          <div style={{ display: "flex", gap: "6px" }}>
            <div {...getRootProps()} style={{
              flex: 1, cursor: "pointer", padding: "4px 8px",
              background: "rgba(255,215,0,0.06)", border: "1px solid #2A2A2A",
              borderRadius: "6px", fontSize: "10px", color: "#B8B8B8", textAlign: "center"
            }}>
              <input {...getInputProps()} />Replace
            </div>
            <button onClick={deleteResume} style={{
              padding: "4px 8px", background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.2)", borderRadius: "6px",
              fontSize: "10px", color: "#ef4444", cursor: "pointer"
            }}>Delete</button>
          </div>
        </div>
      )}
      {error && <p style={{ fontSize: "11px", color: "#ef4444", marginTop: "4px" }}>{error}</p>}
    </div>
  );
}

// ─── Application Detail Modal ────────────────────────────────────────────────

function AppDetailModal({ app, onClose, onWithdraw }) {
  const STEPS = ["APPLIED", "UNDER_REVIEW", "PHONE_SCREEN", "INTERVIEW"];

  const getStep = (status) => {
    if (["OFFER"].includes(status)) return [...STEPS, "OFFER"];
    if (["REJECTED"].includes(status)) return [...STEPS, "REJECTED"];
    if (["WITHDRAWN"].includes(status)) return [...STEPS, "WITHDRAWN"];
    return [...STEPS, "OFFER"];
  };

  const steps = getStep(app.status);
  const currentIdx = steps.indexOf(app.status);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: "680px" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="modal-title">{app.role}</div>
            <div style={{ fontSize: "13px", color: "#777", marginTop: "2px" }}>{app.company}</div>
          </div>
          <button onClick={onClose} style={{
            background: "none", border: "none", color: "#777",
            fontSize: "20px", cursor: "pointer", lineHeight: 1
          }}>✕</button>
        </div>

        <div className="modal-body" style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Summary */}
          <div style={{
            display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px",
            background: "#0B0B0B", borderRadius: "10px", padding: "16px"
          }}>
            <div>
              <div style={{ fontSize: "11px", color: "#777", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>Applied Date</div>
              <div style={{ fontSize: "15px", fontWeight: 600, color: "#fff" }}>
                {app.applied_date ? new Date(app.applied_date).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—"}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "11px", color: "#777", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>Current Status</div>
              <StatusBadge status={app.status} />
            </div>
            {app.notes && (
              <div style={{ gridColumn: "1/-1" }}>
                <div style={{ fontSize: "11px", color: "#777", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>Notes</div>
                <div style={{ fontSize: "13px", color: "#B8B8B8", lineHeight: 1.6 }}>{app.notes}</div>
              </div>
            )}
          </div>

          {/* Journey */}
          <div>
            <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#FFD700", marginBottom: "14px" }}>
              Application Journey
            </h3>
            <div style={{ display: "flex", alignItems: "center", gap: "0" }}>
              {steps.map((step, idx) => {
                const passed = idx <= currentIdx;
                const current = idx === currentIdx;
                const label = STATUS_CONFIG[step]?.label || step;
                return (
                  <div key={step} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", position: "relative" }}>
                    {idx > 0 && (
                      <div style={{
                        position: "absolute", top: "12px", left: "-50%", right: "50%",
                        height: "2px",
                        background: passed ? "linear-gradient(90deg, #D4AF37, #FFD700)" : "#1F1F1F"
                      }} />
                    )}
                    <div style={{
                      width: 24, height: 24, borderRadius: "50%",
                      background: current ? "#FFD700" : passed ? "rgba(212,175,55,0.3)" : "#1F1F1F",
                      border: current ? "2px solid #FFD700" : passed ? "2px solid #D4AF37" : "2px solid #2A2A2A",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: "11px", fontWeight: 700, color: current ? "#050505" : passed ? "#D4AF37" : "#555",
                      zIndex: 1, boxShadow: current ? "0 0 12px rgba(255,215,0,0.5)" : "none"
                    }}>
                      {passed ? (current ? "●" : "✓") : "○"}
                    </div>
                    <div style={{
                      fontSize: "10px", fontWeight: 500, marginTop: "6px", textAlign: "center",
                      color: current ? "#FFD700" : passed ? "#D4AF37" : "#555",
                      lineHeight: 1.3, maxWidth: "60px"
                    }}>
                      {label}
                    </div>
                  </div>
                );
              })}
            </div>
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
                <div>
                  <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>Round</div>
                  <div style={{ color: "#E8E8E8", fontWeight: 500 }}>{app.interview_details.interview_round || "—"}</div>
                </div>
                <div>
                  <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>Type</div>
                  <div style={{ color: "#E8E8E8", fontWeight: 500 }}>{app.interview_details.interview_type || "—"}</div>
                </div>
                <div>
                  <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>Date</div>
                  <div style={{ color: "#E8E8E8", fontWeight: 500 }}>{app.interview_details.interview_date || "—"}</div>
                </div>
                <div>
                  <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>Time</div>
                  <div style={{ color: "#E8E8E8", fontWeight: 500 }}>{app.interview_details.interview_time || "—"}</div>
                </div>
                {app.interview_details.interviewer && (
                  <div>
                    <div style={{ color: "#777", fontSize: "11px", marginBottom: "2px" }}>Interviewer</div>
                    <div style={{ color: "#E8E8E8", fontWeight: 500 }}>{app.interview_details.interviewer}</div>
                  </div>
                )}
                {app.interview_details.meeting_link && (
                  <div style={{ gridColumn: "1/-1" }}>
                    <a
                      href={app.interview_details.meeting_link}
                      target="_blank" rel="noreferrer"
                      className="btn-gold"
                      style={{ padding: "8px 16px", fontSize: "12px", textDecoration: "none", display: "inline-flex" }}
                    >
                      🔗 Join Interview
                    </a>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Status Timeline */}
          <div>
            <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#FFD700", marginBottom: "14px" }}>
              Status Timeline
            </h3>
            {app.status_history && app.status_history.length > 0 ? (
              <div className="timeline">
                {app.status_history.map((h, i) => (
                  <div key={h.id || i} className="timeline-item">
                    <div className="timeline-dot" />
                    <div style={{ fontSize: "13px", fontWeight: 600, color: "#E8E8E8" }}>
                      {h.old_status
                        ? `${STATUS_CONFIG[h.old_status]?.label || h.old_status} → ${STATUS_CONFIG[h.new_status]?.label || h.new_status}`
                        : `Application Submitted (${STATUS_CONFIG[h.new_status]?.label || h.new_status})`}
                    </div>
                    <div style={{ fontSize: "11px", color: "#777", marginTop: "2px" }}>
                      {new Date(h.changed_at).toLocaleString()}
                    </div>
                    {h.notes && (
                      <div style={{
                        fontSize: "12px", color: "#B8B8B8",
                        background: "#0B0B0B", borderRadius: "6px",
                        padding: "8px 10px", marginTop: "6px", fontStyle: "italic"
                      }}>
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
        </div>

        <div className="modal-footer">
          {!["WITHDRAWN", "REJECTED"].includes(app.status) && (
            <button
              className="btn-danger"
              onClick={() => onWithdraw(app.id)}
            >
              Withdraw Application
            </button>
          )}
          <button className="btn-outline-gold" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

// ─── Withdraw Confirm Modal ──────────────────────────────────────────────────

function WithdrawModal({ onConfirm, onCancel }) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" style={{ maxWidth: "400px" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-body" style={{ textAlign: "center", padding: "36px 24px" }}>
          <div style={{ fontSize: "40px", marginBottom: "16px" }}>⚠️</div>
          <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#fff", marginBottom: "8px" }}>
            Withdraw Application?
          </h2>
          <p style={{ fontSize: "14px", color: "#777", lineHeight: 1.6, marginBottom: "24px" }}>
            Are you sure you want to withdraw this application? This action will update your status to WITHDRAWN.
          </p>
          <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
            <button className="btn-outline-gold" onClick={onCancel}>Cancel</button>
            <button className="btn-danger" onClick={onConfirm}>Withdraw Application</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Applications Page ───────────────────────────────────────────────────────

export default function Applications() {
  const [searchParams, setSearchParams] = useSearchParams();

  const applications = useApplicationStore((s) => s.applications);
  const loading = useApplicationStore((s) => s.loading);
  const error = useApplicationStore((s) => s.error);
  const filters = useApplicationStore((s) => s.filters);
  const pagination = useApplicationStore((s) => s.pagination);
  const fetchApplications = useApplicationStore((s) => s.fetchApplications);
  const setStatusFilter = useApplicationStore((s) => s.setStatusFilter);
  const setSearchFilter = useApplicationStore((s) => s.setSearchFilter);
  const setSort = useApplicationStore((s) => s.setSort);
  const setPage = useApplicationStore((s) => s.setPage);

  const [selectedApp, setSelectedApp] = useState(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [withdrawTarget, setWithdrawTarget] = useState(null);

  // Listen for custom open event (from Dashboard "View" button)
  useEffect(() => {
    const handler = async (e) => {
      const appItem = e.detail;
      setDetailOpen(true);
      setLoadingDetail(true);
      try {
        const res = await api.get(`/api/applications/${appItem.id}`, {
          skipErrorHandler: true,
        });
        setSelectedApp(res.data);
      } catch {
        setSelectedApp(appItem);
      } finally {
        setLoadingDetail(false);
      }
    };
    window.addEventListener("open-candidate-app-detail", handler);
    return () => window.removeEventListener("open-candidate-app-detail", handler);
  }, []);

  // Init from URL
  useEffect(() => {
    const s = searchParams.get("status") || "";
    const q = searchParams.get("search") || "";
    const sort = searchParams.get("sort") || "newest";
    const page = Number(searchParams.get("page")) || 1;
    if (s !== filters.status) setStatusFilter(s);
    if (q !== filters.search) setSearchFilter(q);
    if (sort !== filters.sort) setSort(sort);
    if (page !== pagination.page) setPage(page);
  }, []);

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications, filters.status, filters.search, filters.sort, pagination.page]);

  const handleStatusChange = (value) => {
    const status = value === "ALL" ? "" : value;
    setStatusFilter(status);
    const p = new URLSearchParams(searchParams);
    status ? p.set("status", status) : p.delete("status");
    p.delete("page");
    setSearchParams(p);
  };

  const handleSearchChange = (e) => {
    const search = e.target.value;
    setSearchFilter(search);
    const p = new URLSearchParams(searchParams);
    search ? p.set("search", search) : p.delete("search");
    p.delete("page");
    setSearchParams(p);
  };

  const handleSortChange = (value) => {
    setSort(value);
    const p = new URLSearchParams(searchParams);
    value && value !== "newest" ? p.set("sort", value) : p.delete("sort");
    p.delete("page");
    setSearchParams(p);
  };

  const openDetail = async (app) => {
    setDetailOpen(true);
    setLoadingDetail(true);
    try {
      const res = await api.get(`/api/applications/${app.id}`, {
        skipErrorHandler: true,
      });
      setSelectedApp(res.data);
    } catch {
      setSelectedApp(app);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleWithdraw = async (appId) => {
    setWithdrawTarget(appId);
  };

  const confirmWithdraw = async () => {
    try {
      await api.put(`/api/applications/${withdrawTarget}`, { status: "WITHDRAWN" }, { skipErrorHandler: true });
      toast.success("Application withdrawn successfully.");
      setDetailOpen(false);
      setWithdrawTarget(null);
      fetchApplications();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to withdraw.");
    }
  };

  const exportCSV = () => {
    const headers = ["Company", "Role", "Status", "Applied Date", "Notes"];
    const rows = applications.map((a) => [a.company, a.role, a.status, a.applied_date, a.notes]);
    const csv = [headers, ...rows].map((r) => r.map((v) => `"${String(v ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
    const link = Object.assign(document.createElement("a"), {
      href: URL.createObjectURL(new Blob([csv], { type: "text/csv" })),
      download: "applications.csv"
    });
    document.body.appendChild(link); link.click(); document.body.removeChild(link);
  };

  const statuses = Object.keys(STATUS_CONFIG);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h1 style={{ fontSize: "26px", fontWeight: 800, color: "#fff", marginBottom: "4px" }}>
            My Applications
          </h1>
          <p style={{ color: "#777", fontSize: "14px" }}>
            {pagination.total ?? applications.length} applications tracked
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={exportCSV}
            disabled={applications.length === 0}
            className="btn-outline-gold"
            style={{ padding: "8px 16px", fontSize: "13px" }}
          >
            📥 Export CSV
          </button>
          <Link to="/applications/add" className="btn-gold" style={{ textDecoration: "none", padding: "8px 16px", fontSize: "13px" }}>
            + Add Application
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div style={{
        background: "#111111", border: "1px solid #1F1F1F",
        borderRadius: "12px", padding: "16px 20px",
        display: "flex", gap: "14px", flexWrap: "wrap", alignItems: "flex-end"
      }}>
        {/* Search */}
        <div style={{ flex: "1 1 200px", minWidth: "160px" }}>
          <label className="label-gold">Search</label>
          <div style={{ position: "relative" }}>
            <span style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "#777", fontSize: "14px" }}>🔍</span>
            <input
              className="input-gold"
              placeholder="Company or role..."
              value={filters.search}
              onChange={handleSearchChange}
              style={{ paddingLeft: "36px" }}
            />
          </div>
        </div>

        {/* Status */}
        <div style={{ flex: "1 1 150px", minWidth: "140px" }}>
          <label className="label-gold">Status</label>
          <select
            className="input-gold"
            value={filters.status || "ALL"}
            onChange={(e) => handleStatusChange(e.target.value)}
          >
            <option value="ALL">All Statuses</option>
            {statuses.map((s) => (
              <option key={s} value={s}>{STATUS_CONFIG[s].label}</option>
            ))}
          </select>
        </div>

        {/* Sort */}
        <div style={{ flex: "1 1 140px", minWidth: "130px" }}>
          <label className="label-gold">Sort</label>
          <select
            className="input-gold"
            value={filters.sort}
            onChange={(e) => handleSortChange(e.target.value)}
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="company">By Company</option>
          </select>
        </div>

        {(filters.status || filters.search) && (
          <button
            className="btn-outline-gold"
            style={{ padding: "8px 14px", fontSize: "13px", alignSelf: "flex-end" }}
            onClick={() => { setStatusFilter(""); setSearchFilter(""); setSearchParams({}); }}
          >
            ✕ Clear Filters
          </button>
        )}
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

      {/* Table */}
      <div style={{
        background: "#111111", border: "1px solid #1F1F1F",
        borderRadius: "12px", overflow: "hidden"
      }}>
        {loading ? (
          <div style={{ padding: "60px 24px", display: "flex", flexDirection: "column", alignItems: "center", gap: "20px" }}>
            <div className="spinner-gold" />
            <span style={{ color: "#777", fontSize: "14px" }}>Loading applications...</span>
          </div>
        ) : error ? (
          <div style={{ padding: "60px 24px", display: "flex", flexDirection: "column", alignItems: "center", gap: "16px", textAlign: "center" }}>
            <div style={{ fontSize: "40px" }}>⚠️</div>
            <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#fff", margin: 0 }}>
              Couldn't load applications
            </h3>
            <p style={{ color: "#777", fontSize: "13px", margin: 0 }}>
              {error}
            </p>
            <button
              className="btn-outline-gold"
              style={{ padding: "8px 18px", fontSize: "13px" }}
              onClick={() => fetchApplications()}
            >
              Try Again
            </button>
          </div>
        ) : applications.length === 0 ? (
          <div style={{ padding: "80px 24px", textAlign: "center" }}>
            <div style={{ fontSize: "48px", marginBottom: "16px" }}>🗂️</div>
            <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#fff", marginBottom: "8px" }}>
              {filters.status || filters.search ? "No Applications Found" : "No Applications Yet"}
            </h3>
            <p style={{ color: "#777", fontSize: "14px", marginBottom: "24px" }}>
              {filters.status || filters.search
                ? "Applications matching your filters will appear here."
                : "Start tracking your job applications today."}
            </p>
            {filters.status || filters.search ? (
              <button
                className="btn-outline-gold"
                onClick={() => { setStatusFilter(""); setSearchFilter(""); setSearchParams({}); }}
              >
                Clear Filters
              </button>
            ) : (
              <Link to="/applications/add" className="btn-gold" style={{ textDecoration: "none" }}>
                + Add Your First Application
              </Link>
            )}
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="premium-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Job Role</th>
                  <th>Status</th>
                  <th>Applied Date</th>
                  <th>Resume</th>
                  <th>Notes</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((app) => (
                  <tr key={app.id} style={{ opacity: app.optimistic ? 0.6 : 1 }}>
                    <td style={{ color: "#fff", fontWeight: 600, maxWidth: "140px" }}>{app.company}</td>
                    <td style={{ maxWidth: "160px" }}>{app.role}</td>
                    <td><StatusBadge status={app.status} /></td>
                    <td>{app.applied_date ? new Date(app.applied_date).toLocaleDateString() : "—"}</td>
                    <td><ResumeCell application={app} /></td>
                    <td style={{ maxWidth: "140px", fontSize: "12px", color: "#777" }}>
                      <span title={app.notes} style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", display: "block" }}>
                        {app.notes || "—"}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: "8px" }}>
                        <button
                          className="btn-outline-gold"
                          style={{ padding: "6px 12px", fontSize: "12px" }}
                          onClick={() => openDetail(app)}
                        >
                          View
                        </button>
                        {!["WITHDRAWN", "REJECTED"].includes(app.status) && (
                          <button
                            className="btn-danger"
                            style={{ padding: "6px 12px", fontSize: "12px" }}
                            onClick={() => setWithdrawTarget(app.id)}
                          >
                            Withdraw
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {!loading && !error && applications.length > 0 && (
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          background: "#111111", border: "1px solid #1F1F1F",
          borderRadius: "10px", padding: "12px 20px", flexWrap: "wrap", gap: "12px"
        }}>
          <div style={{ fontSize: "13px", color: "#777" }}>
            Page {pagination.page} of {pagination.pages || 1} &nbsp;·&nbsp; {pagination.total || applications.length} total
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button
              className="btn-outline-gold"
              style={{ padding: "6px 14px", fontSize: "13px" }}
              disabled={!pagination.has_prev}
              onClick={() => { const p = pagination.page - 1; setPage(p); const sp = new URLSearchParams(searchParams); sp.set("page", p); setSearchParams(sp); }}
            >
              ← Prev
            </button>
            <button
              className="btn-outline-gold"
              style={{ padding: "6px 14px", fontSize: "13px" }}
              disabled={!pagination.has_next}
              onClick={() => { const p = pagination.page + 1; setPage(p); const sp = new URLSearchParams(searchParams); sp.set("page", p); setSearchParams(sp); }}
            >
              Next →
            </button>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {detailOpen && (
        loadingDetail ? (
          <div className="modal-overlay">
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "16px" }}>
              <div className="spinner-gold" style={{ width: 48, height: 48 }} />
              <span style={{ color: "#777" }}>Loading details...</span>
            </div>
          </div>
        ) : selectedApp ? (
          <AppDetailModal
            app={selectedApp}
            onClose={() => setDetailOpen(false)}
            onWithdraw={handleWithdraw}
          />
        ) : null
      )}

      {/* Withdraw Confirm */}
      {withdrawTarget && (
        <WithdrawModal
          onConfirm={confirmWithdraw}
          onCancel={() => setWithdrawTarget(null)}
        />
      )}
    </div>
  );
}
