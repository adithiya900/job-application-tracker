import { useEffect, useState } from "react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import api from "../services/api";

function ChartSkeleton() {
  return (
    <div className="h-[320px] w-full animate-pulse rounded-md bg-muted" />
  );
}

function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    document.title = "Dashboard - Job Application Tracker";

    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await api.get("/api/analytics");

        setAnalytics(response.data);
      } catch (err) {
        console.error("Failed to fetch analytics:", err);

        setError(
          err.response?.data?.message ||
            "Failed to load analytics data."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  const weeklyData =
    analytics?.applications_per_week?.map((item) => ({
      week: item.week,
      applications: item.count,
    })) || [];

  const statusData = analytics?.by_status
    ? Object.entries(analytics.by_status)
        .filter(([, count]) => count > 0)
        .map(([status, count]) => ({
          name: status,
          value: count,
        }))
    : [];

  const totalApplications = analytics?.total_applications ?? 0;
  const responseRate = analytics?.response_rate ?? 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Analytics Dashboard
        </h1>

        <p className="text-sm text-muted-foreground">
          Track your job application activity and progress.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border bg-card p-5 shadow-sm">
          <p className="text-sm text-muted-foreground">
            Total Applications
          </p>

          {loading ? (
            <div className="mt-2 h-8 w-20 animate-pulse rounded bg-muted" />
          ) : (
            <p className="mt-2 text-3xl font-bold">
              {totalApplications}
            </p>
          )}
        </div>

        <div className="rounded-lg border bg-card p-5 shadow-sm">
          <p className="text-sm text-muted-foreground">
            Response Rate
          </p>

          {loading ? (
            <div className="mt-2 h-8 w-20 animate-pulse rounded bg-muted" />
          ) : (
            <p className="mt-2 text-3xl font-bold">
              {responseRate}%
            </p>
          )}
        </div>
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Applications Per Week */}
        <div className="rounded-lg border bg-card p-5 shadow-sm">
          <div className="mb-4">
            <h2 className="text-lg font-semibold">
              Applications Per Week
            </h2>

            <p className="text-sm text-muted-foreground">
              Number of applications submitted each week.
            </p>
          </div>

          <div className="h-[320px] w-full">
            {loading ? (
              <ChartSkeleton />
            ) : weeklyData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                No weekly application data available.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={weeklyData}
                  margin={{
                    top: 10,
                    right: 20,
                    left: 0,
                    bottom: 10,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />

                  <XAxis dataKey="week" />

                  <YAxis allowDecimals={false} />

                  <Tooltip />

                  <Legend />

                  <Bar
                    dataKey="applications"
                    name="Applications"
                    isAnimationActive
                    animationDuration={800}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Applications By Status */}
        <div className="rounded-lg border bg-card p-5 shadow-sm">
          <div className="mb-4">
            <h2 className="text-lg font-semibold">
              Applications By Status
            </h2>

            <p className="text-sm text-muted-foreground">
              Distribution of your applications by status.
            </p>
          </div>

          <div className="h-[320px] w-full">
            {loading ? (
              <ChartSkeleton />
            ) : statusData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                No status data available.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    isAnimationActive
                    animationDuration={800}
                  >
                    {statusData.map((entry) => (
                      <Cell key={entry.name} />
                    ))}
                  </Pie>

                  <Tooltip />

                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;