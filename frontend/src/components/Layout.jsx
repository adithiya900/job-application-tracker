
import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import ThemeToggle from "./ThemeToggle";

function Layout() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <nav className="flex items-center gap-4 border-b px-4 py-3">
        <div className="flex flex-wrap items-center gap-4">
          <Link to="/">Home</Link>
          <Link to="/login">Login</Link>
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/applications">Applications</Link>
          <Link to="/jobs">Job Search</Link>

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

        <div className="ml-auto">
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
