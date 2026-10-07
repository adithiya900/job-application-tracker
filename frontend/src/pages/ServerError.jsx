export default function ServerError({ error, onRetry }) {
  const handleRetry = () => {
    if (onRetry) {
      onRetry();
      return;
    }

    window.location.reload();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-6">
      <div className="w-full max-w-lg text-center">
        <div className="mb-6 text-7xl font-extrabold tracking-tight text-primary">
          500
        </div>

        <h1 className="text-3xl font-bold mb-3">
          Something went wrong
        </h1>

        <p className="text-muted-foreground mb-6">
          An unexpected error occurred. Please try again.
        </p>

        {import.meta.env.DEV && error?.message && (
          <div className="mb-6 rounded-lg border p-4 text-left text-sm">
            <p className="font-semibold mb-2">Development Error</p>
            <pre className="whitespace-pre-wrap break-words">
              {error.message}
            </pre>
          </div>
        )}

        <div className="flex flex-wrap gap-3 justify-center">
          <button
            type="button"
            onClick={handleRetry}
            className="rounded-md bg-primary px-5 py-2.5 text-primary-foreground hover:opacity-90"
          >
            Try Again
          </button>

          <button
            type="button"
            onClick={() => {
              window.location.href = "/";
            }}
            className="rounded-md border border-input bg-background px-5 py-2.5 text-foreground hover:opacity-90"
          >
            Go Home
          </button>
        </div>
      </div>
    </div>
  );
}
