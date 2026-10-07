import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import useApplicationStore from "../stores/applicationStore";
import toast from "react-hot-toast";

const schema = z.object({
  company: z.string().min(2, "Company name is required"),
  role: z.string().min(2, "Role is required"),
  date: z.string().min(1, "Date is required"),
  notes: z.string().optional(),
});

export default function AddApplication() {
  const location = useLocation();
  const navigate = useNavigate();
  const addApplication = useApplicationStore((s) => s.addApplication);

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [success, setSuccess] = useState(null);

  const trackedJob = location.state?.job;

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      company: "",
      role: "",
      date: new Date().toISOString().split("T")[0],
      notes: "",
    },
  });

  useEffect(() => {
    if (!trackedJob) return;
    const notes = [
      "Tracked from Job Search",
      trackedJob.salary ? `Salary: ${trackedJob.salary}` : "",
      trackedJob.link ? `Job Link: ${trackedJob.link}` : "",
    ].filter(Boolean).join("\n");

    reset({
      company: trackedJob.company || "",
      role: trackedJob.role || "",
      date: new Date().toISOString().split("T")[0],
      notes,
    });
  }, [trackedJob, reset]);

  const onSubmit = async (data) => {
    try {
      setSubmitting(true);
      setSubmitError("");
      setSuccess(null);

      const created = await addApplication({
        company: data.company,
        role: data.role,
        status: "APPLIED",
        notes: data.notes || "",
        applied_date: data.date,
      });

      setSuccess(created);
      toast.success(`✅ Application added: ${created.company} — ${created.role}`);

      setTimeout(() => navigate("/applications"), 1500);
    } catch (err) {
      setSubmitError(err.response?.data?.error || "Failed to create application. Please try again.");
      toast.error("Failed to add application");
    } finally {
      setSubmitting(false);
    }
  };

  const notesValue = watch("notes") || "";

  return (
    <div style={{ maxWidth: "640px" }}>
      {/* Header */}
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "26px", fontWeight: 800, color: "#fff", marginBottom: "6px" }}>
          Add Application
        </h1>
        <p style={{ color: "#777", fontSize: "14px" }}>
          Track a new job application in your pipeline.
        </p>
      </div>

      {/* Job tracked banner */}
      {trackedJob && (
        <div style={{
          background: "rgba(255,215,0,0.06)", border: "1px solid rgba(255,215,0,0.2)",
          borderRadius: "10px", padding: "14px 16px", marginBottom: "20px",
          display: "flex", gap: "12px", alignItems: "center"
        }}>
          <span style={{ fontSize: "20px" }}>🔍</span>
          <div>
            <div style={{ fontSize: "13px", fontWeight: 600, color: "#FFD700" }}>Job tracked from Job Search</div>
            <div style={{ fontSize: "12px", color: "#B8B8B8", marginTop: "2px" }}>
              {trackedJob.company} — {trackedJob.role}
            </div>
          </div>
        </div>
      )}

      {/* Success */}
      {success && (
        <div style={{
          background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.3)",
          borderRadius: "10px", padding: "14px 16px", marginBottom: "20px",
          display: "flex", gap: "10px", alignItems: "center", color: "#22c55e"
        }}>
          <span style={{ fontSize: "20px" }}>🎉</span>
          <div>
            <div style={{ fontWeight: 600, fontSize: "13px" }}>Application added successfully!</div>
            <div style={{ fontSize: "12px", marginTop: "2px" }}>{success.company} — {success.role} · Redirecting...</div>
          </div>
        </div>
      )}

      {/* Error */}
      {submitError && (
        <div style={{
          background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)",
          borderRadius: "10px", padding: "12px 14px", color: "#ef4444",
          fontSize: "13px", marginBottom: "20px",
          display: "flex", alignItems: "center", gap: "8px"
        }}>
          <span>⚠</span> {submitError}
        </div>
      )}

      {/* Form Card */}
      <div style={{
        background: "#111111", border: "1px solid #1F1F1F",
        borderRadius: "16px", padding: "32px 28px"
      }}>
        <form onSubmit={handleSubmit(onSubmit)} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Company */}
          <div>
            <label className="label-gold">Company Name *</label>
            <input
              className={`input-gold ${errors.company ? "border-red-500" : ""}`}
              placeholder="e.g. Google, Microsoft"
              {...register("company")}
            />
            {errors.company && (
              <p style={{ fontSize: "12px", color: "#ef4444", marginTop: "4px" }}>{errors.company.message}</p>
            )}
          </div>

          {/* Role */}
          <div>
            <label className="label-gold">Job Role *</label>
            <input
              className={`input-gold ${errors.role ? "border-red-500" : ""}`}
              placeholder="e.g. Software Engineer, Product Manager"
              {...register("role")}
            />
            {errors.role && (
              <p style={{ fontSize: "12px", color: "#ef4444", marginTop: "4px" }}>{errors.role.message}</p>
            )}
          </div>

          {/* Status info */}
          <div style={{
            background: "rgba(212,175,55,0.06)", border: "1px solid rgba(212,175,55,0.15)",
            borderRadius: "8px", padding: "12px 14px",
            display: "flex", gap: "10px", alignItems: "center"
          }}>
            <span>📝</span>
            <span style={{ fontSize: "12px", color: "#D4AF37" }}>
              New applications are created with <strong>APPLIED</strong> status.
            </span>
          </div>

          {/* Date */}
          <div>
            <label className="label-gold">Application Date *</label>
            <input
              type="date"
              className={`input-gold ${errors.date ? "border-red-500" : ""}`}
              {...register("date")}
            />
            {errors.date && (
              <p style={{ fontSize: "12px", color: "#ef4444", marginTop: "4px" }}>{errors.date.message}</p>
            )}
          </div>

          {/* Notes */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
              <label className="label-gold" style={{ margin: 0 }}>Notes</label>
              <span style={{ fontSize: "11px", color: "#555" }}>{notesValue.length} chars</span>
            </div>
            <textarea
              className="input-gold"
              placeholder="Recruiter contact, salary info, source link, etc."
              rows={4}
              style={{ resize: "vertical" }}
              {...register("notes")}
            />
          </div>

          {/* Actions */}
          <div style={{ display: "flex", gap: "12px", paddingTop: "8px" }}>
            <button
              type="submit"
              className="btn-gold"
              disabled={submitting}
              style={{ flex: 1, justifyContent: "center", padding: "13px" }}
            >
              {submitting ? (
                <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{
                    width: 16, height: 16, border: "2px solid rgba(5,5,5,0.3)",
                    borderTop: "2px solid #050505", borderRadius: "50%",
                    animation: "spin 0.8s linear infinite", display: "inline-block"
                  }} />
                  Submitting...
                </span>
              ) : "Submit Application"}
            </button>
            <button
              type="button"
              className="btn-outline-gold"
              onClick={() => navigate("/applications")}
              style={{ padding: "13px 20px" }}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
