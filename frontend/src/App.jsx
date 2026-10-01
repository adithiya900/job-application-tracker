
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "next-themes";

import { Toaster } from "@/components/ui/sonner";
import { Toaster as HotToaster } from "react-hot-toast";

import Layout from "./components/Layout";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Applications from "./pages/Applications";
import ComponentsDemo from "./pages/ComponentsDemo";
import AddApplication from "./pages/AddApplication";
import JobSearch from "./pages/JobSearch";

import { ApplicationProvider } from "./contexts/ApplicationContext";
import { NotificationProvider } from "./contexts/NotificationContext";
import { AuthProvider } from "./contexts/AuthContext";
import PrivateRoute from "./routes/PrivateRoute";

function App() {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
    >
      <Toaster />
      <HotToaster position="top-right" />

      <BrowserRouter>
        <AuthProvider>
          <NotificationProvider>
          <ApplicationProvider>
            <Routes>
              <Route path="/" element={<Layout />}>
                <Route index element={<Home />} />

                <Route path="login" element={<Login />} />

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
                    path="components-demo"
                    element={<ComponentsDemo />}
                  />
                </Route>
              </Route>
            </Routes>
          </ApplicationProvider>
          </NotificationProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;

