import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

function Layout() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div>
      <nav>
        <Link to="/">Home</Link>{" "}
        <Link to="/login">Login</Link>{" "}
        <Link to="/dashboard">Dashboard</Link>{" "}
        <Link to="/applications">Applications</Link>{" "}

        {isAuthenticated && (
          <button type="button" onClick={handleLogout}>
            Logout
          </button>
        )}
      </nav>

      <main>
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;