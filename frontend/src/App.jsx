
import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "next-themes";

import { Toaster } from "@/components/ui/sonner";
import { Toaster as HotToaster } from "react-hot-toast";

import Layout from "./components/Layout";
const Home = lazy(() => import("./pages/Home"));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Applications = lazy(() => import("./pages/Applications"));
const ComponentsDemo = lazy(() => import("./pages/ComponentsDemo"));
const AddApplication = lazy(() => import("./pages/AddApplication"));
const JobSearch = lazy(() => import("./pages/JobSearch"));
const HRDashboard = lazy(() => import("./pages/HRDashboard"));
const HRAnalytics = lazy(() => import("./pages/HRAnalytics"));
const HRReminders = lazy(() => import("./pages/HRReminders"));
const AdminDashboard = lazy(() => import("./pages/AdminDashboard"));
const AdminReports = lazy(() => import("./pages/AdminReports"));
const Settings = lazy(() => import("./pages/Settings"));
const NotFound = lazy(() => import("./pages/NotFound"));


import { ApplicationProvider } from "./contexts/ApplicationContext";
import { NotificationProvider } from "./contexts/NotificationContext";
import { AuthProvider } from "./contexts/AuthContext";
import PrivateRoute from "./routes/PrivateRoute";
import HRRoute from "./routes/HRRoute";
import AdminRoute from "./routes/AdminRoute";

function App() {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
    >
      <Toaster />
      <HotToaster position="top-right" />

      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <AuthProvider>
          <NotificationProvider>
          <ApplicationProvider>
            <Suspense
                fallback={
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", background: "#0a0a0a" }}>
                    <div className="spinner-gold" style={{ width: 48, height: 48 }} />
                  </div>
                }
              >
                <Routes>
              <Route path="/" element={<Layout />}>
                <Route index element={<Home />} />

                <Route path="login" element={<Login />} />
                <Route path="register" element={<Register />} />

                <Route element={<PrivateRoute />}>
                  <Route
                    path="dashboard"
                    element={<Dashboard />}
                  />

                  <Route
                    path="applications"
                    element={<Applications />}
                  />

                  <Route
                    path="applications/add"
                    element={<AddApplication />}
                  />

                  <Route
                    path="jobs"
                    element={<JobSearch />}
                  />

                  <Route
                    path="settings"
                    element={<Settings />}
                  />

                  <Route element={<HRRoute />}>
                    <Route path="hr" element={<HRDashboard />} />
                    <Route path="hr/analytics" element={<HRAnalytics />} />
                    <Route path="hr/reminders" element={<HRReminders />} />
                  </Route>

                  <Route element={<AdminRoute />}>
                    <Route path="admin" element={<AdminDashboard />} />
                    <Route path="admin/users" element={<AdminDashboard />} />
                    <Route path="admin/applications" element={<AdminDashboard />} />
                    <Route path="admin/interviews" element={<AdminDashboard />} />
                    <Route path="admin/feedback" element={<AdminDashboard />} />
                    <Route path="admin/activity" element={<AdminDashboard />} />
                    <Route path="admin/reports" element={<AdminReports />} />
                  </Route>

                  <Route
                    path="components-demo"
                    element={<ComponentsDemo />}
                  />

                </Route>

                <Route path="*" element={<NotFound />} />
              </Route>
            </Routes>
              </Suspense>
          </ApplicationProvider>
          </NotificationProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
