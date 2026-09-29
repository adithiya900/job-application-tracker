import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "next-themes";

import { Toaster } from "@/components/ui/sonner";

import Layout from "./components/Layout";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Applications from "./pages/Applications";
import ComponentsDemo from "./pages/ComponentsDemo";
import AddApplication from "./pages/AddApplication";

import { ApplicationProvider } from "./contexts/ApplicationContext";
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

      <BrowserRouter>
        <AuthProvider>
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
                    path="components-demo"
                    element={<ComponentsDemo />}
                  />

                  <Route
                    path="applications/add"
                    element={<AddApplication />}
                  />
                </Route>
              </Route>
            </Routes>
          </ApplicationProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;