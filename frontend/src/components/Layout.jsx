import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

const pageTitles = {
  "/dashboard": "Dashboard",
  "/applications": "My Applications",
  "/applications/add": "Add Application",
  "/jobs": "Job Search",
  "/settings": "Settings",
  "/hr": "HR Portal",
  "/admin": "Admin Overview",
  "/admin/users": "User Management",
  "/admin/applications": "Application Management",
  "/admin/interviews": "Interview Management",
  "/admin/feedback": "Interview Feedback",
  "/admin/activity": "Activity Log",
  "/login": "Login",
  "/register": "Register",
};

function Layout() {
  const { isAuthenticated } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const pageTitle = pageTitles[location.pathname] || (
    location.pathname.startsWith("/admin/") ? "Admin Portal" : ""
  );

  const isAuthPage = ["/login", "/register"].includes(location.pathname) || location.pathname === "/";

  if (!isAuthenticated || isAuthPage) {
    return <Outlet />;
  }

  return (
    <div className="app-layout">
      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />

      <div className="main-content">
        <Topbar
          onMenuClick={() => setMobileOpen(true)}
          pageTitle={pageTitle}
        />
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default Layout;
