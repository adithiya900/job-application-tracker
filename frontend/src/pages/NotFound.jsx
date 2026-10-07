import { Link, useNavigate } from "react-router-dom";

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-6">
      <div className="w-full max-w-lg text-center">
        <div className="mb-6 text-7xl font-extrabold tracking-tight text-primary">
          404
        </div>

        <h1 className="text-3xl font-bold mb-3">
          Page Not Found
        </h1>

        <p className="text-muted-foreground mb-8">
          The page you're looking for doesn't exist or may have been moved.
        </p>

        <div className="flex flex-wrap gap-3 justify-center">
          <Link
            to="/"
            className="rounded-md bg-primary px-5 py-2.5 text-primary-foreground hover:opacity-90"
          >
            Go Home
          </Link>

          <button
            type="button"
            onClick={() => navigate(-1)}
            className="rounded-md border border-input bg-background px-5 py-2.5 text-foreground hover:opacity-90"
          >
            Go Back
          </button>
        </div>
      </div>
    </div>
  );
}
