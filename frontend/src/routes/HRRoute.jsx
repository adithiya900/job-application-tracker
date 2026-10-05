import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import toast from "react-hot-toast";
import { useEffect } from "react";

function HRRoute() {
  const { user, isAuthenticated } = useAuth();

  const isHR = user?.role === "HR" || user?.role === "ADMIN";

  useEffect(() => {
    if (isAuthenticated && !isHR) {
      toast.error("Access denied: HR permissions required");
    }
  }, [isAuthenticated, isHR]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!isHR) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

export default HRRoute;
