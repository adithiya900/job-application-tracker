import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const user = await register(name, email, password);
      const isHR = user?.role === "HR" || user?.role === "ADMIN";
      navigate(isHR ? "/hr" : "/dashboard");
    } catch (err) {
      setError(err.response?.data?.error || err.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #050505 0%, #0B0B0B 50%, #050505 100%)",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: "32px 24px",
      fontFamily: "'Inter', system-ui, sans-serif"
    }}>
      <div style={{ width: "100%", maxWidth: "440px" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div style={{
            width: 56, height: 56, margin: "0 auto 16px",
            borderRadius: "14px",
            background: "linear-gradient(135deg, #FFD700, #D4AF37)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "26px", boxShadow: "0 0 30px rgba(255,215,0,0.3)"
          }}>💼</div>
          <h1 style={{ fontSize: "26px", fontWeight: 800, color: "#fff", marginBottom: "6px", letterSpacing: "-0.03em" }}>
            Create your account
          </h1>
          <p style={{ fontSize: "14px", color: "#777" }}>
            Start tracking your job applications today
          </p>
        </div>

        <div style={{
          background: "#111111", border: "1px solid #2A2A2A",
          borderRadius: "20px", padding: "36px 32px",
          boxShadow: "0 0 60px rgba(0,0,0,0.5)"
        }}>
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

          <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label className="label-gold">Full Name</label>
              <input
                type="text"
                className="input-gold"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoComplete="name"
              />
            </div>

            <div>
              <label className="label-gold">Email Address</label>
              <input
                type="email"
                className="input-gold"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label className="label-gold">Password</label>
              <div style={{ position: "relative" }}>
                <input
                  type={showPassword ? "text" : "password"}
                  className="input-gold"
                  placeholder="Min. 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  autoComplete="new-password"
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

            <button
              type="submit"
              className="btn-gold"
              disabled={loading}
              style={{
                width: "100%", justifyContent: "center",
                padding: "13px", fontSize: "15px", marginTop: "8px"
              }}
            >
              {loading ? (
                <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{
                    width: 16, height: 16, border: "2px solid rgba(5,5,5,0.3)",
                    borderTop: "2px solid #050505", borderRadius: "50%",
                    animation: "spin 0.8s linear infinite", display: "inline-block"
                  }} />
                  Creating account...
                </span>
              ) : "Create Account →"}
            </button>
          </form>

          <p style={{ textAlign: "center", marginTop: "24px", fontSize: "14px", color: "#777" }}>
            Already have an account?{" "}
            <Link to="/login" style={{ color: "#FFD700", fontWeight: 600, textDecoration: "none" }}>
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Register;