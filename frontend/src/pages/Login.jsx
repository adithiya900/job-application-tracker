import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

// Credentials kept on this device only when "Remember me" is ticked.
// This is a convenience encoding, NOT encryption: anyone with access to this
// browser profile can read it back. A browser password manager is the secure
// alternative, which is why the inputs also carry proper autofill metadata.
const REMEMBER_EMAIL_KEY = "remembered_email";
const REMEMBER_PASSWORD_KEY = "remembered_password";

const encodeCredential = (value) => btoa(encodeURIComponent(value));
const decodeCredential = (value) => {
  try {
    return decodeURIComponent(atob(value));
  } catch {
    return "";
  }
};

const features = [
  { icon: "🎯", text: "Apply for jobs & track every application" },
  { icon: "📊", text: "Monitor application progress in real-time" },
  { icon: "🔔", text: "Receive instant status update notifications" },
  { icon: "📅", text: "Manage interviews & meeting schedules" },
  { icon: "🏆", text: "Track hiring decisions from offer to start" },
];

function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState(() => localStorage.getItem(REMEMBER_EMAIL_KEY) || "");
  const [password, setPassword] = useState(() => decodeCredential(localStorage.getItem(REMEMBER_PASSWORD_KEY) || ""));
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(
    () => !!localStorage.getItem(REMEMBER_EMAIL_KEY)
  );

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const loggedInUser = await login(email, password);

      if (rememberMe) {
        localStorage.setItem(REMEMBER_EMAIL_KEY, email);
        localStorage.setItem(REMEMBER_PASSWORD_KEY, encodeCredential(password));
      } else {
        localStorage.removeItem(REMEMBER_EMAIL_KEY);
        localStorage.removeItem(REMEMBER_PASSWORD_KEY);
      }

      const destination = loggedInUser?.role === "ADMIN"
        ? "/admin"
        : loggedInUser?.role === "HR"
          ? "/hr"
          : "/dashboard";
      navigate(destination);
    } catch (err) {
      setError(err.response?.data?.error || err.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #050505 0%, #0B0B0B 50%, #050505 100%)",
      display: "flex",
      fontFamily: "'Inter', system-ui, sans-serif"
    }}>
      {/* Left Panel */}
      <div style={{
        flex: 1, display: "flex", flexDirection: "column",
        justifyContent: "center", padding: "60px 80px",
        background: "linear-gradient(135deg, #0A0800 0%, #050500 100%)",
        borderRight: "1px solid #1A1A0A",
        position: "relative", overflow: "hidden"
      }}
        className="hidden lg:flex"
      >
        {/* Background glow */}
        <div style={{
          position: "absolute", top: "20%", left: "20%",
          width: "400px", height: "400px",
          background: "radial-gradient(circle, rgba(255,215,0,0.08) 0%, transparent 70%)",
          borderRadius: "50%", pointerEvents: "none"
        }} />

        <div style={{ position: "relative", zIndex: 1 }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: "14px", marginBottom: "60px" }}>
            <div style={{
              width: 52, height: 52, borderRadius: "14px",
              background: "linear-gradient(135deg, #FFD700 0%, #D4AF37 100%)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "26px", boxShadow: "0 0 30px rgba(255,215,0,0.3)"
            }}>💼</div>
            <div>
              <div style={{ fontSize: "22px", fontWeight: 800, color: "#FFD700", letterSpacing: "-0.03em" }}>
                Job Application
              </div>
              <div style={{ fontSize: "14px", color: "#D4AF37", fontWeight: 500 }}>
                Tracker
              </div>
            </div>
          </div>

          {/* Tagline */}
          <h1 style={{
            fontSize: "42px", fontWeight: 800, color: "#fff",
            lineHeight: 1.1, marginBottom: "16px", letterSpacing: "-0.04em"
          }}>
            Connect.{" "}
            <span style={{ color: "#FFD700" }}>Apply.</span>
            <br />Get Hired.
          </h1>
          <p style={{ fontSize: "16px", color: "#777", marginBottom: "48px", lineHeight: 1.7 }}>
            The premium platform for tracking your career journey from application to offer.
          </p>

          {/* Features */}
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {features.map((f, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: "14px"
              }}>
                <div style={{
                  width: 36, height: 36, borderRadius: "8px",
                  background: "rgba(255,215,0,0.1)", border: "1px solid rgba(255,215,0,0.2)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "16px", flexShrink: 0
                }}>
                  {f.icon}
                </div>
                <span style={{ fontSize: "14px", color: "#B8B8B8" }}>{f.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Panel - Login Card */}
      <div style={{
        flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
        padding: "32px 24px"
      }}>
        <div style={{
          width: "100%", maxWidth: "420px"
        }}>
          {/* Mobile Logo */}
          <div style={{ textAlign: "center", marginBottom: "32px" }} className="lg:hidden">
            <div style={{ fontSize: "32px", marginBottom: "8px" }}>💼</div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "#FFD700" }}>Job Application Tracker</div>
          </div>

          <div style={{
            background: "#111111", border: "1px solid #2A2A2A",
            borderRadius: "20px", padding: "40px 36px",
            boxShadow: "0 0 60px rgba(0,0,0,0.5)"
          }}>
            <h2 style={{
              fontSize: "24px", fontWeight: 700, color: "#fff",
              marginBottom: "6px"
            }}>
              Welcome back 👋
            </h2>
            <p style={{ fontSize: "14px", color: "#777", marginBottom: "28px" }}>
              Sign in to your account to continue
            </p>

            {/* Error */}
            {error && (
              <div style={{
                background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)",
                borderRadius: "10px", padding: "12px 14px",
                color: "#ef4444", fontSize: "13px", marginBottom: "20px",
                display: "flex", alignItems: "center", gap: "8px"
              }}>
                <span>⚠</span> {error}
              </div>
            )}

            <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
              {/* Email */}
              <div>
                <label className="label-gold">Email Address</label>
                <input
                  type="email"
                  name="email"
                  className="input-gold"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  autoCorrect="off"
                  autoCapitalize="none"
                  spellCheck="false"
                />
              </div>

              {/* Password */}
              <div>
                <label className="label-gold">Password</label>
                <div style={{ position: "relative" }}>
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    className="input-gold"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    style={{ paddingRight: "44px" }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: "absolute", right: "12px", top: "50%",
                      transform: "translateY(-50%)",
                      background: "none", border: "none",
                      color: "#777", cursor: "pointer", fontSize: "16px"
                    }}
                  >
                    {showPassword ? "🙈" : "👁"}
                  </button>
                </div>
              </div>

               {/* Remember me & Submit */}
               <div>
                 <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                   <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                     <input
                       type="checkbox"
                       name="remember"
                       checked={rememberMe}
                       onChange={(e) => setRememberMe(e.target.checked)}
                       style={{ width: "16px", height: "16px", cursor: "pointer" }}
                     />
                     <span style={{ fontSize: "13px", color: "#B8B8B8" }}>Remember me</span>
                   </label>
                   {rememberMe && (
                     <button
                       type="button"
                       onClick={() => {
                         localStorage.removeItem(REMEMBER_EMAIL_KEY);
                         localStorage.removeItem(REMEMBER_PASSWORD_KEY);
                         setRememberMe(false);
                         setEmail("");
                         setPassword("");
                       }}
                       style={{
                         background: "none", border: "none", padding: 0,
                         color: "#777", fontSize: "11px", cursor: "pointer",
                         textDecoration: "underline"
                       }}
                       title="Delete the credentials stored on this device"
                     >
                       Forget saved login
                     </button>
                   )}
                 </div>
                 <p style={{ fontSize: "11px", color: "#666", lineHeight: 1.5 }}>
                   {rememberMe
                     ? "Your email and password are stored on this device only, so both fields are filled automatically next time."
                     : "Tick this to auto-fill your email and password next time on this device."}
                 </p>
               </div>

               {/* Submit */}
               <button
                 type="submit"
                 className="btn-gold"
                 disabled={loading}
                 style={{
                   width: "100%", justifyContent: "center",
                   padding: "13px", fontSize: "15px", marginTop: "4px"
                 }}
               >
                {loading ? (
                  <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{
                      width: 16, height: 16, border: "2px solid rgba(5,5,5,0.3)",
                      borderTop: "2px solid #050505", borderRadius: "50%",
                      animation: "spin 0.8s linear infinite", display: "inline-block"
                    }} />
                    Signing in...
                  </span>
                ) : "Sign In →"}
              </button>
            </form>

            <p style={{ textAlign: "center", marginTop: "24px", fontSize: "14px", color: "#777" }}>
              Don't have an account?{" "}
              <Link to="/register" style={{ color: "#FFD700", fontWeight: 600, textDecoration: "none" }}>
                Create Account
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;