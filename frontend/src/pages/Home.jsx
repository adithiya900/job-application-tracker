import { Link } from "react-router-dom";

function Home() {
  return (
    <main style={{
      minHeight: "100vh",
      background: "var(--bg-primary)",
      color: "var(--text-primary)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "32px 24px",
      fontFamily: "'Inter', system-ui, sans-serif",
    }}>
      <section style={{
        width: "100%",
        maxWidth: "760px",
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "20px",
        padding: "clamp(28px, 6vw, 64px)",
        textAlign: "center",
      }}>
        <div style={{ fontSize: "14px", color: "var(--primary)", letterSpacing: "0.16em", textTransform: "uppercase", marginBottom: "18px" }}>
          Job Application Tracker
        </div>
        <h1 style={{ fontSize: "clamp(32px, 7vw, 56px)", fontWeight: 800, color: "var(--text-primary)", marginBottom: "16px" }}>
          Your next opportunity, organized.
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "16px", maxWidth: "540px", margin: "0 auto 32px" }}>
          Keep every application, interview, and hiring update in one place.
        </p>
        <div style={{ display: "flex", justifyContent: "center", gap: "12px", flexWrap: "wrap" }}>
          <Link to="/login" className="btn-gold" style={{ textDecoration: "none", padding: "12px 22px" }}>
            Sign In
          </Link>
          <Link to="/register" className="btn-outline-gold" style={{ textDecoration: "none", padding: "12px 22px" }}>
            Create Account
          </Link>
        </div>
      </section>
    </main>
  );
}

export default Home;
