import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const CandidateNav = [
  { to: "/dashboard", icon: "⊞", label: "Dashboard" },
  { to: "/applications", icon: "📋", label: "My Applications" },
  { to: "/applications/add", icon: "＋", label: "Add Application" },
  { to: "/jobs", icon: "🔍", label: "Job Search" },
  { to: "/settings", icon: "⚙", label: "Profile & Settings" },
];

const HRNav = [
  { to: "/hr", icon: "⊞", label: "HR Dashboard" },
  { to: "/settings", icon: "⚙", label: "Profile & Settings" },
];

const AdminNav = [
  { to: "/admin", icon: "⊞", label: "Overview" },
  { to: "/admin/users", icon: "♙", label: "User Management" },
  { to: "/admin/applications", icon: "▤", label: "Applications" },
  { to: "/admin/interviews", icon: "◷", label: "Interviews" },
  { to: "/admin/feedback", icon: "✎", label: "Feedback" },
  { to: "/jobs", icon: "⌕", label: "Job Search" },
  { to: "/admin/activity", icon: "◴", label: "Activity Log" },
  { to: "/settings", icon: "⚙", label: "Profile & Settings" },
];

export default function Sidebar({ mobileOpen, onClose }) {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const isAdmin = user?.role === "ADMIN";
  const isHR = user?.role === "HR";
  const navItems = isAdmin ? AdminNav : isHR ? HRNav : CandidateNav;

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  if (!isAuthenticated) return null;

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/70 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`sidebar ${mobileOpen ? "open" : ""}`}
        style={{ boxShadow: "4px 0 30px rgba(0,0,0,0.5)" }}
      >
        {/* Logo */}
        <div className="sidebar-logo">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{
              width: 36, height: 36, borderRadius: "8px",
              background: "linear-gradient(135deg, #FFD700, #D4AF37)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "18px", flexShrink: 0
            }}>💼</div>
            <div>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "#FFD700", lineHeight: 1.2 }}>
                Job Tracker
              </div>
              <div style={{ fontSize: "11px", color: "#777", marginTop: "2px" }}>
                {isAdmin ? "Admin Portal" : isHR ? "HR Portal" : "Candidate Portal"}
              </div>
            </div>
          </div>
        </div>

        {/* User Info */}
        <div style={{ padding: "16px 20px", borderBottom: "1px solid #1A1A1A" }}>
          <div style={{
            background: "rgba(255,215,0,0.06)", border: "1px solid #2A2A2A",
            borderRadius: "10px", padding: "12px"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{
                width: 32, height: 32, borderRadius: "50%",
                background: "linear-gradient(135deg, #D4AF37, #8B7523)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "13px", fontWeight: 700, color: "#050505", flexShrink: 0
              }}>
                {user?.name?.charAt(0)?.toUpperCase() || "U"}
              </div>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: "13px", fontWeight: 600, color: "#FFD700", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {user?.name || "User"}
                </div>
                <div style={{ fontSize: "11px", color: "#A88A2A", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {user?.email || ""}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="sidebar-nav">
          {navItems.map(({ to, icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/hr" || to === "/admin"}
              onClick={onClose}
              style={({ isActive }) => isActive ? {} : {}}
              className={({ isActive }) => isActive ? "active" : ""}
            >
              <span style={{ fontSize: "16px", width: 20, textAlign: "center" }}>{icon}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <button
            onClick={handleLogout}
            style={{
              display: "flex", alignItems: "center", gap: "10px",
              padding: "10px 14px", borderRadius: "8px",
              background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)",
              color: "#ef4444", fontSize: "14px", fontWeight: 500,
              cursor: "pointer", width: "100%", transition: "all 0.2s"
            }}
            onMouseEnter={e => e.currentTarget.style.background = "rgba(239,68,68,0.15)"}
            onMouseLeave={e => e.currentTarget.style.background = "rgba(239,68,68,0.08)"}
          >
            <span style={{ fontSize: "16px" }}>⏻</span>
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
}
