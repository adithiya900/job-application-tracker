
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function JobSearch() {
  const navigate = useNavigate();

  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("Chennai");
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);

  // =========================
  // Debounced Job Search
  // =========================
  useEffect(() => {
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      setJobs([]);
      setError("");
      setLoading(false);
      setPage(1);
      setHasNext(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        setError("");
        setPage(1);

        const response = await api.get("/api/jobs/search", {
          params: {
            q: trimmedQuery,
            location: location.trim(),
            page: 1,
            per_page: 5,
          },
        });

        const data = response.data;
        const results = data.jobs || [];

        setJobs(results);

        // Backend returns 5 jobs per page.
        // If fewer than 5 are returned, there is no next page.
        setHasNext(results.length === 5);
      } catch (searchError) {
        console.error("Job search failed:", searchError);

        setJobs([]);

        setError(
          searchError.response?.data?.error ||
            "Failed to search jobs. Please try again."
        );

        setHasNext(false);
      } finally {
        setLoading(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [query, location]);

  // =========================
  // Load More Jobs
  // =========================
  const handleLoadMore = async () => {
    if (loading || !query.trim()) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      const nextPage = page + 1;

      const response = await api.get("/api/jobs/search", {
        params: {
          q: query.trim(),
          location: location.trim(),
          page: nextPage,
          per_page: 5,
        },
      });

      const data = response.data;
      const results = data.jobs || [];

      setJobs((previousJobs) => [
        ...previousJobs,
        ...results,
      ]);

      setPage(nextPage);

      setHasNext(results.length === 5);
    } catch (searchError) {
      console.error("Loading more jobs failed:", searchError);

      setError(
        searchError.response?.data?.error ||
          "Failed to load more jobs."
      );
    } finally {
      setLoading(false);
    }
  };

  // =========================
  // Track Job
  // =========================
  const handleTrackJob = (job) => {
    navigate("/applications/add", {
      state: {
        job: {
          company: job.company || "",
          role: job.title || "",
          salary: job.salary_range || "",
          link: job.redirect_url || "",
        },
      },
    });
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold">
          Job Search
        </h1>

        <p className="text-sm text-muted-foreground">
          Search for jobs and track interesting opportunities.
        </p>
      </div>

      {/* Search Inputs */}
      <div className="flex flex-col gap-4 md:flex-row">
        <div className="flex-1">
          <label
            htmlFor="job-search"
            className="mb-2 block text-sm font-medium"
          >
            Search Jobs
          </label>

          <input
            id="job-search"
            type="text"
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
            placeholder="React Developer Chennai"
            className="w-full rounded-md border bg-background px-3 py-2"
          />
        </div>

        <div className="md:w-[220px]">
          <label
            htmlFor="job-location"
            className="mb-2 block text-sm font-medium"
          >
            Location
          </label>

          <input
            id="job-location"
            type="text"
            value={location}
            onChange={(event) =>
              setLocation(event.target.value)
            }
            placeholder="Chennai"
            className="w-full rounded-md border bg-background px-3 py-2"
          />
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <p className="text-sm text-muted-foreground">
          Searching jobs...
        </p>
      )}

      {/* Error */}
      {error && (
        <p className="text-sm text-destructive">
          {error}
        </p>
      )}

      {/* Empty State */}
      {!loading &&
        query.trim() &&
        jobs.length === 0 &&
        !error && (
          <p className="text-sm text-muted-foreground">
            No jobs found.
          </p>
        )}

      {/* Job Results */}
      <div className="grid gap-4">
        {jobs.map((job, index) => (
          <div
            key={`${job.company}-${job.title}-${index}`}
            className="rounded-lg border p-5"
          >
            <div className="space-y-2">
              <h2 className="text-lg font-semibold">
                {job.title || "Job title not available"}
              </h2>

              <p className="text-sm font-medium">
                {job.company || "Company not available"}
              </p>

              <p className="text-sm text-muted-foreground">
                Location:{" "}
                {job.location || "Location not specified"}
              </p>

              <p className="text-sm text-muted-foreground">
                Salary:{" "}
                {job.salary_range || "Not disclosed"}
              </p>
            </div>

            {/* Job Actions */}
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => handleTrackJob(job)}
                className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
              >
                Track this job
              </button>

              {job.redirect_url && (
                <a
                  href={job.redirect_url}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
                >
                  View Job
                </a>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Load More */}
      {hasNext && (
        <div className="flex justify-center">
          <button
            type="button"
            onClick={handleLoadMore}
            disabled={loading}
            className="rounded-md border px-5 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Loading..." : "Load More"}
          </button>
        </div>
      )}
    </div>
  );
}

export default JobSearch;
