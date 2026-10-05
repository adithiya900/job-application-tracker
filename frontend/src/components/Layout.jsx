
import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useNotifications } from "../contexts/NotificationContext";
import ThemeToggle from "./ThemeToggle";

function Layout() {
  const { user, isAuthenticated, logout } = useAuth();
  const { unreadCount, markAllRead } = useNotifications();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const isHR = user?.role === "HR" || user?.role === "ADMIN";

  return (
    <div className="min-h-screen bg-background text-foreground">
      <nav className="flex items-center gap-4 border-b px-4 py-3">
        <div className="flex flex-wrap items-center gap-4">
          <Link to="/" className="font-semibold text-primary">JobTracker</Link>
          {!isAuthenticated && <Link to="/login">Login</Link>}
          {isAuthenticated && (
            <>
              <Link to="/dashboard">Dashboard</Link>
              <Link to="/applications">My Applications</Link>
              <Link to="/jobs">Job Search</Link>
              <Link to="/settings">Settings</Link>
              {isHR && (
                <Link to="/hr" className="font-semibold text-purple-600 dark:text-purple-400">
                  HR Portal
                </Link>
              )}
            </>
          )}

          {isAuthenticated && (
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md border px-3 py-1.5 text-sm"
            >
              Logout
            </button>
          )}
        </div>

        <div className="ml-auto flex items-center gap-3">
          {isAuthenticated && (
            <div className="relative">
              <button
                type="button"
                onClick={markAllRead}
                className="relative rounded-md border px-3 py-1.5 text-sm"
                title="Mark all notifications as read"
              >
                🔔

                {unreadCount > 0 && (
                  <span className="absolute -right-2 -top-2 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-xs text-white">
                    {unreadCount}
                  </span>
                )}
              </button>
            </div>
          )}

          <ThemeToggle />
        </div>
      </nav>

      <main className="mx-auto w-full max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
