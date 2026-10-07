import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

export default function JobSearch() {
  const navigate = useNavigate();

  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("Chennai");
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);

  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) { setJobs([]); setError(""); setLoading(false); setPage(1); setHasNext(false); return; }

    const timer = setTimeout(async () => {
      try {
        setLoading(true); setError(""); setPage(1);
        const res = await api.get("/api/jobs/search", { skipErrorHandler: true, params: { q: trimmed, location: location.trim(), page: 1, per_page: 5 } });
        const results = res.data.jobs || [];
        setJobs(results);
        setHasNext(results.length === 5);
      } catch (err) {
        setJobs([]);
        setError(err.response?.data?.error || "Failed to search jobs. Please try again.");
        setHasNext(false);
      } finally {
        setLoading(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [query, location]);

  const handleLoadMore = async () => {
    if (loading || !query.trim()) return;
    try {
      setLoading(true); setError("");
      const nextPage = page + 1;
      const res = await api.get("/api/jobs/search", { skipErrorHandler: true, params: { q: query.trim(), location: location.trim(), page: nextPage, per_page: 5 } });
      const results = res.data.jobs || [];
      setJobs((prev) => [...prev, ...results]);
      setPage(nextPage);
      setHasNext(results.length === 5);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to load more jobs.");
    } finally {
      setLoading(false);
    }
  };

  const handleTrack = (job) => {
    navigate("/applications/add", {
      state: { job: { company: job.company || "", role: job.title || "", salary: job.salary_range || "", link: job.redirect_url || "" } }
    });
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: "26px", fontWeight: 800, color: "#fff", marginBottom: "6px" }}>Job Search 🔍</h1>
        <p style={{ color: "#777", fontSize: "14px" }}>Search for jobs and track interesting opportunities.</p>
      </div>

      {/* Search Bar */}
      <div style={{
        background: "#111111", border: "1px solid #1F1F1F",
        borderRadius: "14px", padding: "20px 24px",
        display: "flex", gap: "14px", flexWrap: "wrap", alignItems: "flex-end"
      }}>
        <div style={{ flex: "2 1 240px", minWidth: "200px" }}>
          <label className="label-gold">Search Jobs</label>
          <div style={{ position: "relative" }}>
            <span style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "#777", fontSize: "16px" }}>🔍</span>
            <input
              className="input-gold"
              placeholder="React Developer, Data Analyst..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{ paddingLeft: "40px" }}
            />
          </div>
        </div>
        <div style={{ flex: "1 1 160px", minWidth: "140px" }}>
          <label className="label-gold">Location</label>
          <div style={{ position: "relative" }}>
            <span style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "#777", fontSize: "14px" }}>📍</span>
            <input
              className="input-gold"
              placeholder="Chennai"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              style={{ paddingLeft: "36px" }}
            />
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && jobs.length === 0 && (
        <div style={{ display: "flex", alignItems: "center", gap: "14px", padding: "24px 0" }}>
          <div className="spinner-gold" style={{ width: 24, height: 24 }} />
          <span style={{ color: "#777", fontSize: "14px" }}>Searching jobs...</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{
          background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)",
          borderRadius: "10px", padding: "14px 16px", color: "#ef4444", fontSize: "13px"
        }}>
          ⚠ {error}
        </div>
      )}

      {/* Empty */}
      {!loading && query.trim() && jobs.length === 0 && !error && (
        <div style={{ textAlign: "center", padding: "60px 24px" }}>
          <div style={{ fontSize: "40px", marginBottom: "12px" }}>🔍</div>
          <div style={{ fontSize: "16px", fontWeight: 600, color: "#fff", marginBottom: "6px" }}>No jobs found</div>
          <p style={{ color: "#777", fontSize: "13px", marginBottom: "18px" }}>
            Try changing your search keywords or filters.
          </p>
          <button
            className="btn-outline-gold"
            style={{ padding: "8px 18px", fontSize: "13px" }}
            onClick={() => { setQuery(""); setLocation("Chennai"); }}
          >
            Clear Search
          </button>
        </div>
      )}

      {/* Empty initial */}
      {!query.trim() && !loading && (
        <div style={{ textAlign: "center", padding: "60px 24px" }}>
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>💼</div>
          <div style={{ fontSize: "18px", fontWeight: 600, color: "#fff", marginBottom: "8px" }}>Start searching for jobs</div>
          <p style={{ color: "#777", fontSize: "14px" }}>Type a job title or skill to find opportunities near you.</p>
        </div>
      )}

      {/* Results */}
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        {jobs.map((job, idx) => (
          <div
            key={`${job.company}-${job.title}-${idx}`}
            className="premium-card"
            style={{ padding: "20px 24px" }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
              <div style={{ flex: 1, minWidth: "200px" }}>
                <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#fff", marginBottom: "4px" }}>
                  {job.title || "Job title not available"}
                </h3>
                <div style={{ fontSize: "14px", fontWeight: 600, color: "#D4AF37", marginBottom: "6px" }}>
                  {job.company || "Company not available"}
                </div>
                <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
                  {job.location && (
                    <span style={{ fontSize: "12px", color: "#777" }}>
                      📍 {job.location}
                    </span>
                  )}
                  {job.salary_range && (
                    <span style={{ fontSize: "12px", color: "#777" }}>
                      💰 {job.salary_range}
                    </span>
                  )}
                </div>
              </div>
              <div style={{ display: "flex", gap: "10px", flexShrink: 0 }}>
                {job.redirect_url && (
                  <a
                    href={job.redirect_url}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-outline-gold"
                    style={{ textDecoration: "none", padding: "8px 14px", fontSize: "13px" }}
                  >
                    View Job
                  </a>
                )}
                <button
                  className="btn-gold"
                  style={{ padding: "8px 14px", fontSize: "13px" }}
                  onClick={() => handleTrack(job)}
                >
                  Track Job
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Load More */}
      {hasNext && (
        <div style={{ textAlign: "center" }}>
          <button
            className="btn-outline-gold"
            onClick={handleLoadMore}
            disabled={loading}
            style={{ padding: "10px 28px" }}
          >
            {loading ? "Loading..." : "Load More Jobs"}
          </button>
        </div>
      )}
    </div>
  );
}
