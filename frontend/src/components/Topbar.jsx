import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useNotifications } from "../contexts/NotificationContext";

function timeAgo(dateStr) {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function Topbar({ onMenuClick, pageTitle }) {
  const { user, logout } = useAuth();
  const { notifications, unreadCount, markAllRead } = useNotifications();
  const navigate = useNavigate();
  const [panelOpen, setPanelOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const panelRef = useRef(null);
  const profileRef = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setPanelOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleBellClick = () => {
    setPanelOpen((v) => !v);
    if (!panelOpen && unreadCount > 0) {
      // mark read when opening
    }
  };

  return (
    <header className="topbar" style={{ justifyContent: "space-between" }}>
      {/* Left: Hamburger + Title */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <button
          onClick={onMenuClick}
          style={{
            background: "none", border: "none", color: "#E6C65C",
            fontSize: "22px", cursor: "pointer", padding: "4px",
            display: "flex", alignItems: "center"
          }}
          aria-label="Toggle menu"
          className="md:hidden"
        >
          ☰
        </button>
        {pageTitle && (
          <span style={{ fontSize: "16px", fontWeight: 600, color: "#FFD700" }}>
            {pageTitle}
          </span>
        )}
      </div>

      {/* Right: Notifications + User */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>

        {/* Notification Bell */}
        <div style={{ position: "relative" }} ref={panelRef}>
          <button
            onClick={handleBellClick}
            aria-label="Notifications"
            style={{
              background: panelOpen ? "rgba(255,215,0,0.12)" : "transparent",
              border: "1px solid " + (panelOpen ? "#D4AF37" : "#2A2A2A"),
              borderRadius: "8px", padding: "7px 10px",
              cursor: "pointer", color: panelOpen ? "#FFD700" : "#E6C65C",
              fontSize: "18px", position: "relative", transition: "all 0.2s"
            }}
          >
            🔔
            {unreadCount > 0 && (
              <span style={{
                position: "absolute", top: "-6px", right: "-6px",
                background: "#FFD700", color: "#050505",
                borderRadius: "50%", minWidth: "18px", height: "18px",
                fontSize: "10px", fontWeight: 700,
                display: "flex", alignItems: "center", justifyContent: "center",
                padding: "0 3px"
              }}>
                {unreadCount > 99 ? "99+" : unreadCount}
              </span>
            )}
          </button>

          {/* Notification Panel */}
          {panelOpen && (
            <div className="notification-panel">
              <div style={{
                padding: "14px 16px", borderBottom: "1px solid #1F1F1F",
                display: "flex", alignItems: "center", justifyContent: "space-between"
              }}>
                <span style={{ fontWeight: 600, fontSize: "14px", color: "#FFD700" }}>
                  🔔 Notifications
                </span>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllRead}
                    style={{
                      background: "none", border: "none",
                      color: "#D4AF37", fontSize: "12px",
                      cursor: "pointer", fontWeight: 500
                    }}
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div style={{ maxHeight: "360px", overflowY: "auto" }}>
                {notifications.length === 0 ? (
                  <div style={{
                    padding: "32px 16px", textAlign: "center",
                    color: "#A88A2A", fontSize: "13px"
                  }}>
                    <div style={{ fontSize: "28px", marginBottom: "8px" }}>🔕</div>
                    No new notifications
                  </div>
                ) : (
                  notifications.slice(0, 20).map((n) => (
                    <div
                      key={n.id}
                      className={`notification-item ${!n.read ? "unread" : ""}`}
                    >
                      <div style={{ fontSize: "13px", color: "#E6C65C", lineHeight: 1.5 }}>
                        {n.message}
                      </div>
                      <div style={{ fontSize: "11px", color: "#A88A2A", marginTop: "4px" }}>
                        {n.timestamp ? timeAgo(n.timestamp) : "Just now"}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Profile Dropdown */}
        <div style={{ position: "relative" }} ref={profileRef}>
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            style={{
              background: profileOpen ? "rgba(255,215,0,0.12)" : "transparent",
              border: "1px solid " + (profileOpen ? "#D4AF37" : "#2A2A2A"),
              borderRadius: "8px", padding: "6px 10px",
              cursor: "pointer", color: "#E6C65C",
              fontSize: "16px", display: "flex", alignItems: "center", gap: "6px"
            }}
            aria-label="User profile"
          >
            <div style={{
              width: 28, height: 28, borderRadius: "50%",
              background: "linear-gradient(135deg, #D4AF37, #8B7523)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "12px", fontWeight: 700, color: "#050505"
            }}>
              {user?.name?.charAt(0)?.toUpperCase() || "U"}
            </div>
            <span style={{ fontSize: "13px" }} className="hidden sm:inline">
              {user?.name?.split(" ")[0]}
            </span>
            ▼
          </button>

          {profileOpen && (
            <div style={{
              position: "absolute", right: 0, top: "110%",
              width: "220px", background: "#111111",
              border: "1px solid #2A2A2A", borderRadius: "12px",
              padding: "12px", boxShadow: "0 10px 40px rgba(0,0,0,0.5)",
              zIndex: 100
            }}>
              <div style={{ padding: "8px 0" }}>
                <div style={{ fontSize: "13px", fontWeight: 600, color: "#fff", marginBottom: "2px" }}>
                  {user?.name || "Unknown User"}
                </div>
                <div style={{ fontSize: "11px", color: "#777", marginBottom: "4px" }}>
                  {user?.email || "No email"}
                </div>
                <div style={{ fontSize: "11px", color: "#D4AF37", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                  {user?.role || "User"}
                </div>
              </div>
              <div style={{ height: "1px", background: "#1F1F1F", margin: "10px 0" }} />
              <button
                onClick={() => { setProfileOpen(false); navigate("/settings"); }}
                style={{
                  width: "100%", padding: "8px 10px", background: "transparent",
                  border: "none", color: "#B8B8B8", fontSize: "13px",
                  cursor: "pointer", textAlign: "left", borderRadius: "6px",
                  transition: "color 0.2s"
                }}
                onMouseEnter={e => e.currentTarget.style.color = "#fff"}
                onMouseLeave={e => e.currentTarget.style.color = "#B8B8B8"}
              >
                ⚙ Settings
              </button>
              <button
                onClick={() => { setProfileOpen(false); logout(); navigate("/login"); }}
                style={{
                  width: "100%", padding: "8px 10px", background: "transparent",
                  border: "none", color: "#B8B8B8", fontSize: "13px",
                  cursor: "pointer", textAlign: "left", borderRadius: "6px",
                  transition: "color 0.2s"
                }}
                onMouseEnter={e => e.currentTarget.style.color = "#ef4444"}
                onMouseLeave={e => e.currentTarget.style.color = "#B8B8B8"}
              >
                ⏻ Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
