import { useState, useRef, useEffect } from "react";
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
  const { user } = useAuth();
  const { notifications, unreadCount, markAllRead } = useNotifications();
  const [panelOpen, setPanelOpen] = useState(false);
  const panelRef = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setPanelOpen(false);
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

        {/* User Avatar */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{
            width: 32, height: 32, borderRadius: "50%",
            background: "linear-gradient(135deg, #D4AF37, #8B7523)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "13px", fontWeight: 700, color: "#050505"
          }}>
            {user?.name?.charAt(0)?.toUpperCase() || "U"}
          </div>
          <span style={{ fontSize: "13px", color: "#E6C65C", display: "none" }}
            className="sm:block">
            {user?.name?.split(" ")[0]}
          </span>
        </div>
      </div>
    </header>
  );
}
