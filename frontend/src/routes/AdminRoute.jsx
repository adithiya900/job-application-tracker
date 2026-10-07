import { useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../contexts/AuthContext";

function AdminRoute() {
  const { user, isAuthenticated } = useAuth();
  const isAdmin = user?.role === "ADMIN";

  useEffect(() => {
    if (isAuthenticated && !isAdmin) {
      toast.error("Access denied: administrator permissions required");
    }
  }, [isAuthenticated, isAdmin]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  if (!isAdmin) {
    return <Navigate to={user?.role === "HR" ? "/hr" : "/dashboard"} replace />;
  }
  return <Outlet />;
}

export default AdminRoute;
