import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import toast from "react-hot-toast";
import api from "../services/api";
import StatusBadge, { STATUS_CONFIG } from "../components/StatusBadge";

const STATUSES = [
  "APPLIED",
  "UNDER_REVIEW",
  "PHONE_SCREEN",
  "INTERVIEW",
  "OFFER",
  "REJECTED",
  "WITHDRAWN",
];

const TRANSITIONS = {
  APPLIED: ["UNDER_REVIEW", "PHONE_SCREEN", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"],
  UNDER_REVIEW: ["PHONE_SCREEN", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"],
  PHONE_SCREEN: ["INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"],
  INTERVIEW: ["OFFER", "REJECTED", "WITHDRAWN"],
  OFFER: ["REJECTED", "WITHDRAWN"],
  REJECTED: ["APPLIED", "UNDER_REVIEW"],
  WITHDRAWN: ["APPLIED"],
};

const ROLE_LABELS = { USER: "Candidate", HR: "HR", ADMIN: "Admin" };

function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function Panel({ children, style }) {
  return <section className="premium-card" style={{ padding: 20, minWidth: 0, ...style }}>{children}</section>;
}

function PageHeading({ title, subtitle, children }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, flexWrap: "wrap", marginBottom: 22 }}>
      <div>
        <h1 style={{ fontSize: 26, marginBottom: 6 }}>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {children}
    </div>
  );
}

function EmptyState({ children }) {
  return <div style={{ padding: "34px 16px", textAlign: "center", color: "var(--text-muted)" }}>{children}</div>;
}

function formValue(event, name) {
  return event.currentTarget.elements.namedItem(name)?.value || "";
}

function AdminDashboard() {
  const location = useLocation();
  const section = useMemo(() => {
    const current = location.pathname.split("/").filter(Boolean).at(-1);
    return current === "admin" ? "overview" : current;
  }, [location.pathname]);

  const [loadResult, setLoadResult] = useState({ key: null, data: null, error: "" });
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [reloadKey, setReloadKey] = useState(0);
  const [userModal, setUserModal] = useState(null);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const isApplications = ["applications", "interviews", "feedback"].includes(section);
  const requestKey = JSON.stringify({ section, search, role, status, page, reloadKey });
  const loading = loadResult.key !== requestKey;
  const data = loading ? null : loadResult.data;
  const error = loading ? "" : loadResult.error;

  useEffect(() => {
    let active = true;

    const request = section === "overview"
      ? api.get("/api/admin/dashboard", { skipErrorHandler: true })
      : section === "users"
        ? api.get("/api/admin/users", { skipErrorHandler: true, params: { search, role, page, per_page: 20 } })
        : isApplications
          ? api.get("/api/admin/applications", {
            skipErrorHandler: true,
            params: {
              search,
              status,
              view: section === "interviews" || section === "feedback" ? section : "all",
              page,
              per_page: 20,
            },
          })
          : section === "activity"
            ? api.get("/api/admin/activity", { skipErrorHandler: true, params: { search, page, per_page: 20 } })
            : Promise.reject(new Error("Unknown admin page"));

    request.then((response) => {
      if (active) setLoadResult({ key: requestKey, data: response.data, error: "" });
    }).catch((err) => {
      if (active) {
        setLoadResult({
          key: requestKey,
          data: null,
          error: err.response?.data?.error || err.message || "Unable to load this admin view.",
        });
      }
    });

    return () => { active = false; };
  }, [section, search, role, status, page, reloadKey, isApplications, requestKey]);

  const refresh = () => setReloadKey((value) => value + 1);

  const openApplication = useCallback(async (applicationId) => {
    setDetailLoading(true);
    setSelectedApplication({ loading: true, id: applicationId });
    try {
      const response = await api.get(`/api/admin/applications/${applicationId}`, { skipErrorHandler: true });
      setSelectedApplication(response.data);
    } catch (err) {
      setSelectedApplication(null);
      toast.error(err.response?.data?.error || "Unable to load application details.");
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const submitUser = async (event) => {
    event.preventDefault();
    setSaving(true);
    const body = {
      name: userModal.name,
      email: userModal.email,
      role: userModal.role,
    };
    if (!userModal.id || userModal.password) body.password = userModal.password;
    if (userModal.id) body.is_active = userModal.is_active;
    try {
      if (userModal.id) {
        await api.patch(`/api/admin/users/${userModal.id}`, body, { skipErrorHandler: true });
        toast.success("User updated.");
      } else {
        await api.post("/api/admin/users", body, { skipErrorHandler: true });
        toast.success("User created.");
      }
      setUserModal(null);
      refresh();
    } catch (err) {
      toast.error(err.response?.data?.error || "Unable to save user.");
    } finally {
      setSaving(false);
    }
  };

  const deleteUser = async (user) => {
    if (!window.confirm(`Delete ${user.name} and their associated applications? This cannot be undone.`)) return;
    try {
      await api.delete(`/api/admin/users/${user.id}`, { skipErrorHandler: true });
      toast.success("User deleted.");
      refresh();
    } catch (err) {
      toast.error(err.response?.data?.error || "Unable to delete user.");
    }
  };

  const deleteApplication = async () => {
    const application = selectedApplication;
    if (!application || !window.confirm(`Delete ${application.role} at ${application.company} and its history? This cannot be undone.`)) return;
    setSaving(true);
    try {
      await api.delete(`/api/admin/applications/${application.id}`, { skipErrorHandler: true });
      toast.success("Application deleted.");
      setSelectedApplication(null);
      refresh();
    } catch (err) {
      toast.error(err.response?.data?.error || "Unable to delete application.");
    } finally {
      setSaving(false);
    }
  };

  const submitApplicationEdit = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      await api.patch(`/api/admin/applications/${selectedApplication.id}`, {
        company: formValue(event, "company"),
        role: formValue(event, "role"),
        notes: formValue(event, "application_notes"),
        candidate_email: formValue(event, "candidate_email"),
      }, { skipErrorHandler: true });
      toast.success("Application updated.");
      await openApplication(selectedApplication.id);
      refresh();
    } catch (err) {
      toast.error(err.response?.data?.error || "Unable to update application.");
    } finally {
      setSaving(false);
    }
  };

  const submitStatus = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      await api.patch(
        `/api/admin/applications/${selectedApplication.id}/status`,
        { status: formValue(event, "status"), notes: formValue(event, "notes") },
        { skipErrorHandler: true },
      );
      toast.success("Application status updated.");
      await openApplication(selectedApplication.id);
      refresh();
    } catch (err) {
      toast.error(err.response?.data?.error || "Unable to update status.");
    } finally {
      setSaving(false);
    }
  };

  const submitInterview = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      await api.patch(`/api/hr/applications/${selectedApplication.id}/interview`, {
        interview_date: formValue(event, "interview_date") || null,
        interview_time: formValue(event, "interview_time") || null,
        interview_round: formValue(event, "interview_round") || null,
        interview_type: formValue(event, "interview_type") || null,
        meeting_link: formValue(event, "meeting_link") || null,
        interviewer: formValue(event, "interviewer") || null,
        hr_notes: formValue(event, "hr_notes") || null,
      }, { skipErrorHandler: true });
      toast.success("Interview details saved.");
      await openApplication(selectedApplication.id);
      refresh();
    } catch (err) {
      toast.error(err.response?.data?.error || "Unable to save interview details.");
    } finally {
      setSaving(false);
    }
  };

  const submitFeedback = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      await api.post(`/api/hr/applications/${selectedApplication.id}/feedback`, {
        technical_skills: formValue(event, "technical_skills") || null,
        communication: formValue(event, "communication") || null,
        overall_feedback: formValue(event, "overall_feedback") || null,
        recommendation: formValue(event, "recommendation") || null,
        internal_notes: formValue(event, "internal_notes") || null,
      }, { skipErrorHandler: true });
      toast.success("Interview feedback submitted.");
      await openApplication(selectedApplication.id);
      refresh();
    } catch (err) {
      toast.error(err.response?.data?.error || "Unable to submit feedback.");
    } finally {
      setSaving(false);
    }
  };

  const renderStatusFilter = () => (
    <select className="input-gold" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }} style={{ width: "auto", minWidth: 160 }}>
      <option value="">All statuses</option>
      {STATUSES.map((value) => <option key={value} value={value}>{STATUS_CONFIG[value].label}</option>)}
    </select>
  );

  const renderSearch = () => (
    <form onSubmit={(event) => { event.preventDefault(); setSearch(searchInput.trim()); setPage(1); }} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      <input
        className="input-gold"
        value={searchInput}
        onChange={(event) => setSearchInput(event.target.value)}
        placeholder={section === "users" ? "Search name or email" : section === "activity" ? "Search action" : "Search candidate, company, role"}
        aria-label="Search records"
        style={{ width: "min(320px, 100%)" }}
      />
      <button className="btn-outline-gold" type="submit">Search</button>
    </form>
  );

  const renderPagination = (pagination) => pagination && pagination.pages > 1 && (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, paddingTop: 16 }}>
      <span style={{ color: "var(--text-muted)", fontSize: 13 }}>
        Page {pagination.page} of {pagination.pages} · {pagination.total} records
      </span>
      <div style={{ display: "flex", gap: 8 }}>
        <button className="btn-outline-gold" disabled={!pagination.has_prev} onClick={() => setPage((value) => value - 1)}>Previous</button>
        <button className="btn-outline-gold" disabled={!pagination.has_next} onClick={() => setPage((value) => value + 1)}>Next</button>
      </div>
    </div>
  );

  const renderOverview = () => {
    if (!data) return null;
    const statusEntries = Object.entries(data.applications.by_status || {});
    return (
      <>
        <PageHeading title="Admin Overview" subtitle="System-wide accounts, hiring activity, and upcoming interviews.">
          <button className="btn-outline-gold" onClick={refresh}>Refresh data</button>
        </PageHeading>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(185px, 1fr))", gap: 14, marginBottom: 18 }}>
          {[
            ["Total users", data.users.total],
            ["Candidates", data.users.by_role.USER || 0],
            ["HR accounts", data.users.by_role.HR || 0],
            ["Administrators", data.users.by_role.ADMIN || 0],
            ["Applications", data.applications.total],
            ["Interviews", data.interviews.total],
            ["Feedback entries", data.feedback_count],
          ].map(([label, value]) => (
            <Panel key={label} style={{ padding: 18 }}>
              <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 9 }}>{label}</div>
              <div style={{ fontSize: 28, color: "var(--gold)", fontWeight: 750 }}>{value}</div>
            </Panel>
          ))}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 420px), 1fr))", gap: 16 }}>
          <Panel>
            <h2 style={{ fontSize: 17, marginBottom: 14 }}>Applications by status</h2>
            <div style={{ display: "grid", gap: 10 }}>
              {statusEntries.map(([value, count]) => (
                <div key={value} style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                  <StatusBadge status={value} /><strong>{count}</strong>
                </div>
              ))}
            </div>
          </Panel>
          <Panel>
            <h2 style={{ fontSize: 17, marginBottom: 14 }}>Upcoming interviews</h2>
            {data.interviews.upcoming.length ? data.interviews.upcoming.map(({ application, details }) => (
              <button key={application.id} onClick={() => openApplication(application.id)} style={rowButton}>
                <span><strong>{application.candidate?.name || "Candidate"}</strong><br />{application.role} · {application.company}</span>
                <span>{formatDate(details.interview_date)} {details.interview_time || ""}</span>
              </button>
            )) : <EmptyState>No upcoming interviews are scheduled.</EmptyState>}
          </Panel>
          <Panel>
            <h2 style={{ fontSize: 17, marginBottom: 14 }}>Recent applications</h2>
            {data.applications.recent.length ? data.applications.recent.map((application) => (
              <button key={application.id} onClick={() => openApplication(application.id)} style={rowButton}>
                <span><strong>{application.candidate?.name || "Candidate"}</strong><br />{application.role} · {application.company}</span>
                <StatusBadge status={application.status} />
              </button>
            )) : <EmptyState>No applications have been created yet.</EmptyState>}
            <Link to="/admin/applications" style={{ display: "inline-block", marginTop: 12 }}>View all applications</Link>
          </Panel>
          <Panel>
            <h2 style={{ fontSize: 17, marginBottom: 14 }}>Recent status changes</h2>
            {data.recent_status_changes.length ? data.recent_status_changes.map((entry) => (
              <div key={entry.id} style={{ ...rowButton, cursor: "default" }}>
                <span><strong>{entry.application.candidate}</strong><br />{entry.application.role} · {entry.application.company}</span>
                <span>{entry.old_status ? `${STATUS_CONFIG[entry.old_status]?.label || entry.old_status} → ` : ""}{STATUS_CONFIG[entry.new_status]?.label || entry.new_status}</span>
              </div>
            )) : <EmptyState>No status updates have been recorded.</EmptyState>}
          </Panel>
        </div>
      </>
    );
  };

  const renderUsers = () => (
    <>
      <PageHeading title="User Management" subtitle="Create accounts, update profiles and roles, or remove accounts.">
        <button className="btn-gold" onClick={() => setUserModal({ name: "", email: "", password: "", role: "USER" })}>＋ Add user</button>
      </PageHeading>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
        {renderSearch()}
        <select className="input-gold" aria-label="Filter by role" value={role} onChange={(event) => { setRole(event.target.value); setPage(1); }} style={{ width: "auto", minWidth: 150 }}>
          <option value="">All roles</option>
          <option value="USER">Candidate</option>
          <option value="HR">HR</option>
          <option value="ADMIN">Admin</option>
        </select>
      </div>
      <Panel style={{ padding: 0, overflow: "hidden" }}>
        <div style={tableWrap}>
          <table className="premium-table" style={{ minWidth: 760 }}>
            <thead><tr><th>User</th><th>Role</th><th>Account</th><th>Registered</th><th>Applications</th><th>Actions</th></tr></thead>
            <tbody>{(data?.users || []).map((user) => (
              <tr key={user.id}>
                <td><strong>{user.name}</strong><br /><span>{user.email}</span></td>
                <td>{ROLE_LABELS[user.role] || user.role}</td>
                <td>{user.is_active ? "Active" : "Disabled"}</td>
                <td>{formatDate(user.created_at)}</td>
                <td>{user.application_count}</td>
                <td>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button className="btn-outline-gold" onClick={() => setUserModal({ ...user, password: "" })}>Edit</button>
                    <button className="btn-outline-gold" disabled={user.is_current_user} onClick={() => deleteUser(user)}>Delete</button>
                  </div>
                </td>
              </tr>
            ))}</tbody>
          </table>
        </div>
        {!data?.users?.length && <EmptyState>No users match these filters.</EmptyState>}
        <div style={{ padding: "0 16px 16px" }}>{renderPagination(data?.pagination)}</div>
      </Panel>
      <p style={{ marginTop: 12, fontSize: 12 }}>Disabled accounts cannot sign in or use existing access and refresh tokens.</p>
    </>
  );

  const renderApplications = () => (
    <>
      <PageHeading
        title={section === "interviews" ? "Interview Management" : section === "feedback" ? "Interview Feedback" : "Application Management"}
        subtitle="Review system-wide applications and open a record to manage its hiring workflow."
      >
        {renderSearch()}
      </PageHeading>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
        {renderStatusFilter()}
        {section !== "applications" && <Link className="btn-outline-gold" to="/admin/applications">All applications</Link>}
      </div>
      <Panel style={{ padding: 0, overflow: "hidden" }}>
        <div style={tableWrap}>
          <table className="premium-table" style={{ minWidth: 760 }}>
            <thead><tr><th>Candidate</th><th>Company / Role</th><th>Status</th><th>Interview</th><th>Applied</th><th /></tr></thead>
            <tbody>{(data?.applications || []).map((application) => (
              <tr key={application.id}>
                <td><strong>{application.candidate?.name || "Unknown"}</strong><br /><span>{application.candidate?.email || "—"}</span></td>
                <td><strong>{application.company}</strong><br /><span>{application.role}</span></td>
                <td><StatusBadge status={application.status} /></td>
                <td>{application.interview_details ? `${formatDate(application.interview_details.interview_date)} ${application.interview_details.interview_time || ""}` : "—"}</td>
                <td>{formatDate(application.applied_date)}</td>
                <td><button className="btn-outline-gold" onClick={() => openApplication(application.id)}>Details</button></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
        {!data?.applications?.length && <EmptyState>No applications match these filters.</EmptyState>}
        <div style={{ padding: "0 16px 16px" }}>{renderPagination(data?.pagination)}</div>
      </Panel>
    </>
  );

  const renderActivity = () => (
    <>
      <PageHeading title="Activity Log" subtitle="Audited administrator and HR operations across the platform.">
        {renderSearch()}
      </PageHeading>
      <Panel style={{ padding: 0, overflow: "hidden" }}>
        <div style={tableWrap}>
          <table className="premium-table" style={{ minWidth: 700 }}>
            <thead><tr><th>When</th><th>Actor</th><th>Action</th><th>Target</th><th>Details</th></tr></thead>
            <tbody>{(data?.activity || []).map((entry) => (
              <tr key={entry.id}>
                <td>{entry.created_at ? new Date(entry.created_at).toLocaleString() : "—"}</td>
                <td>{entry.admin_name}</td>
                <td>{entry.action.replaceAll("_", " ")}</td>
                <td>{entry.target_user_name || (entry.target_user_id ? `User #${entry.target_user_id}` : "—")}</td>
                <td>{Object.entries(entry.details || {}).map(([key, value]) => `${key.replaceAll("_", " ")}: ${value}`).join(" · ") || "—"}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
        {!data?.activity?.length && <EmptyState>No audited activity has been recorded yet.</EmptyState>}
        <div style={{ padding: "0 16px 16px" }}>{renderPagination(data?.pagination)}</div>
      </Panel>
    </>
  );

  return (
    <div style={{ maxWidth: 1320, margin: "0 auto", minWidth: 0 }}>
      {loading && <div role="status" style={{ padding: 28, color: "var(--gold)" }}>Loading admin data…</div>}
      {!loading && error && (
        <Panel>
          <h1 style={{ fontSize: 22, marginBottom: 8 }}>Unable to load admin data</h1>
          <p role="alert" style={{ marginBottom: 14 }}>{error}</p>
          <button className="btn-outline-gold" onClick={refresh}>Try again</button>
        </Panel>
      )}
      {!loading && !error && section === "overview" && renderOverview()}
      {!loading && !error && section === "users" && renderUsers()}
      {!loading && !error && isApplications && renderApplications()}
      {!loading && !error && section === "activity" && renderActivity()}
      {userModal && (
        <div className="modal-overlay" onClick={() => !saving && setUserModal(null)}>
          <section className="modal-content" role="dialog" aria-modal="true" aria-labelledby="admin-user-title" onClick={(event) => event.stopPropagation()} style={{ maxWidth: 520 }}>
            <div className="modal-header">
              <h2 id="admin-user-title" className="modal-title">{userModal.id ? "Edit user" : "Create user"}</h2>
              <button className="btn-outline-gold" onClick={() => setUserModal(null)} aria-label="Close">×</button>
            </div>
            <form onSubmit={submitUser}>
              <div className="modal-body" style={{ display: "grid", gap: 14 }}>
                <label className="label-gold">Name<input className="input-gold" required maxLength={100} value={userModal.name} onChange={(event) => setUserModal({ ...userModal, name: event.target.value })} /></label>
                <label className="label-gold">Email<input className="input-gold" required type="email" maxLength={120} value={userModal.email} onChange={(event) => setUserModal({ ...userModal, email: event.target.value })} /></label>
                <label className="label-gold">Role
                  <select className="input-gold" value={userModal.role} disabled={userModal.is_current_user} onChange={(event) => setUserModal({ ...userModal, role: event.target.value })}>
                    <option value="USER">Candidate</option><option value="HR">HR</option><option value="ADMIN">Admin</option>
                  </select>
                </label>
                {userModal.id && <label className="label-gold">Account status
                  <select className="input-gold" value={userModal.is_active ? "active" : "disabled"} disabled={userModal.is_current_user} onChange={(event) => setUserModal({ ...userModal, is_active: event.target.value === "active" })}>
                    <option value="active">Active</option><option value="disabled">Disabled</option>
                  </select>
                </label>}
                {!userModal.id && <label className="label-gold">Initial password<input className="input-gold" required minLength={8} type="password" autoComplete="new-password" value={userModal.password} onChange={(event) => setUserModal({ ...userModal, password: event.target.value })} /></label>}
                {userModal.id && <p style={{ fontSize: 12 }}>Password changes are handled by the account owner through Profile &amp; Settings.</p>}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn-outline-gold" disabled={saving} onClick={() => setUserModal(null)}>Cancel</button>
                <button type="submit" className="btn-gold" disabled={saving}>{saving ? "Saving…" : "Save user"}</button>
              </div>
            </form>
          </section>
        </div>
      )}
      {selectedApplication && (
        <div className="modal-overlay" onClick={() => !saving && setSelectedApplication(null)}>
          <section className="modal-content" role="dialog" aria-modal="true" aria-labelledby="admin-app-title" onClick={(event) => event.stopPropagation()} style={{ maxWidth: 920 }}>
            <div className="modal-header">
              <div>
                <h2 id="admin-app-title" className="modal-title">Application details</h2>
                {!detailLoading && selectedApplication.candidate && <p style={{ fontSize: 13 }}>{selectedApplication.candidate.name} · {selectedApplication.company} · {selectedApplication.role}</p>}
              </div>
              <button className="btn-outline-gold" onClick={() => setSelectedApplication(null)} aria-label="Close">×</button>
            </div>
            {detailLoading || selectedApplication.loading ? (
              <div className="modal-body" role="status">Loading application…</div>
            ) : (
              <div className="modal-body" style={{ display: "grid", gap: 20 }}>
                <div style={{ display: "flex", gap: 18, flexWrap: "wrap", alignItems: "center" }}>
                  <span>Candidate: <strong>{selectedApplication.candidate?.name} ({selectedApplication.candidate?.email})</strong></span>
                  <span>Applied: <strong>{formatDate(selectedApplication.applied_date)}</strong></span>
                  <span>Current status: <StatusBadge status={selectedApplication.status} /></span>
                </div>
                <Panel>
                  <h3 style={{ fontSize: 16, marginBottom: 12 }}>Edit application</h3>
                  <form onSubmit={submitApplicationEdit} style={formGrid}>
                    <label className="label-gold">Company<input className="input-gold" name="company" required maxLength={100} defaultValue={selectedApplication.company} /></label>
                    <label className="label-gold">Job role<input className="input-gold" name="role" required maxLength={100} defaultValue={selectedApplication.role} /></label>
                    <label className="label-gold">Candidate email<input className="input-gold" name="candidate_email" type="email" required defaultValue={selectedApplication.candidate?.email || ""} /></label>
                    <label className="label-gold" style={{ gridColumn: "1 / -1" }}>Application notes<textarea className="input-gold" name="application_notes" rows={2} maxLength={5000} defaultValue={selectedApplication.notes || ""} /></label>
                    <button className="btn-gold" type="submit" disabled={saving}>{saving ? "Saving…" : "Save application"}</button>
                  </form>
                  <p style={{ fontSize: 12, marginTop: 8 }}>Reassignment is limited to an active candidate account. The application status and history are preserved.</p>
                </Panel>
                <form onSubmit={submitStatus} style={formGrid}>
                  <label className="label-gold">Next status
                    <select className="input-gold" name="status" defaultValue="" required>
                      <option value="" disabled>Select valid transition</option>
                      {(TRANSITIONS[selectedApplication.status] || []).map((value) => <option key={value} value={value}>{STATUS_CONFIG[value].label}</option>)}
                    </select>
                  </label>
                  <label className="label-gold">Status note<input className="input-gold" name="notes" maxLength={500} placeholder="Optional note in history" /></label>
                  <button className="btn-gold" type="submit" disabled={saving || !(TRANSITIONS[selectedApplication.status] || []).length}>{saving ? "Saving…" : "Update status"}</button>
                </form>

                <div>
                  <h3 style={{ fontSize: 16, marginBottom: 10 }}>Status history</h3>
                  {selectedApplication.status_history?.length ? (
                    <div className="timeline">
                      {selectedApplication.status_history.map((entry) => (
                        <div className="timeline-item" key={entry.id}>
                          <div className="timeline-dot" />
                          <strong>{entry.old_status ? `${STATUS_CONFIG[entry.old_status]?.label || entry.old_status} → ` : ""}{STATUS_CONFIG[entry.new_status]?.label || entry.new_status}</strong>
                          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{entry.changed_by_name || "System"} · {new Date(entry.changed_at).toLocaleString()}</div>
                          {entry.notes && <p>{entry.notes}</p>}
                        </div>
                      ))}
                    </div>
                  ) : <p>No status history is available.</p>}
                </div>

                <Panel>
                  <h3 style={{ fontSize: 16, marginBottom: 12 }}>Interview schedule</h3>
                  <form onSubmit={submitInterview} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 210px), 1fr))", gap: 12 }}>
                    <label className="label-gold">Date<input className="input-gold" type="date" name="interview_date" defaultValue={selectedApplication.interview_details?.interview_date || ""} /></label>
                    <label className="label-gold">Time<input className="input-gold" type="time" name="interview_time" defaultValue={selectedApplication.interview_details?.interview_time || ""} /></label>
                    <label className="label-gold">Round<input className="input-gold" name="interview_round" defaultValue={selectedApplication.interview_details?.interview_round || ""} /></label>
                    <label className="label-gold">Type<select className="input-gold" name="interview_type" defaultValue={selectedApplication.interview_details?.interview_type || ""}><option value="">Select type</option><option>Online</option><option>In-person</option><option>Phone</option></select></label>
                    <label className="label-gold">Interviewer<input className="input-gold" name="interviewer" defaultValue={selectedApplication.interview_details?.interviewer || ""} /></label>
                    <label className="label-gold">Meeting link<input className="input-gold" type="url" name="meeting_link" defaultValue={selectedApplication.interview_details?.meeting_link || ""} /></label>
                    <label className="label-gold" style={{ gridColumn: "1 / -1" }}>Internal interview notes<textarea className="input-gold" name="hr_notes" rows={2} defaultValue={selectedApplication.interview_details?.hr_notes || ""} /></label>
                    <button className="btn-gold" type="submit" disabled={saving}>{saving ? "Saving…" : "Save interview"}</button>
                  </form>
                </Panel>

                <Panel>
                  <h3 style={{ fontSize: 16, marginBottom: 12 }}>Submit interview feedback</h3>
                  <form onSubmit={submitFeedback} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 210px), 1fr))", gap: 12 }}>
                    <label className="label-gold">Technical skills<input className="input-gold" name="technical_skills" /></label>
                    <label className="label-gold">Communication<input className="input-gold" name="communication" /></label>
                    <label className="label-gold">Recommendation<select className="input-gold" name="recommendation" defaultValue=""><option value="">Select recommendation</option><option>Hire</option><option>No Hire</option><option>Maybe</option></select></label>
                    <label className="label-gold" style={{ gridColumn: "1 / -1" }}>Overall feedback<textarea className="input-gold" name="overall_feedback" rows={2} /></label>
                    <label className="label-gold" style={{ gridColumn: "1 / -1" }}>Internal notes<textarea className="input-gold" name="internal_notes" rows={2} /></label>
                    <button className="btn-gold" type="submit" disabled={saving}>{saving ? "Saving…" : "Submit feedback"}</button>
                  </form>
                </Panel>

                <div>
                  <h3 style={{ fontSize: 16, marginBottom: 10 }}>Submitted feedback</h3>
                  {selectedApplication.feedback?.length ? selectedApplication.feedback.map((entry) => (
                    <Panel key={entry.id} style={{ marginBottom: 10 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                        <strong>{entry.recommendation || "Feedback"} · {entry.submitted_by_name || "Interviewer"}</strong>
                        <span>{formatDate(entry.created_at)}</span>
                      </div>
                      <p style={{ marginTop: 8 }}>{entry.overall_feedback || "No written feedback."}</p>
                      {entry.internal_notes && <p style={{ marginTop: 8 }}>Internal notes: {entry.internal_notes}</p>}
                    </Panel>
                  )) : <p>No feedback has been submitted.</p>}
                </div>
              </div>
            )}
            <div className="modal-footer" style={{ justifyContent: "space-between" }}>
              {!selectedApplication.loading && <button className="btn-outline-gold" disabled={saving} onClick={deleteApplication}>Delete application</button>}
              <button className="btn-outline-gold" onClick={() => setSelectedApplication(null)}>Close</button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

const rowButton = {
  width: "100%",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  textAlign: "left",
  gap: 12,
  padding: "12px 0",
  border: 0,
  borderBottom: "1px solid var(--border)",
  background: "transparent",
  cursor: "pointer",
};

const tableWrap = { width: "100%", overflowX: "auto" };
const formGrid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 220px), 1fr))",
  gap: 12,
  alignItems: "end",
};

export default AdminDashboard;
