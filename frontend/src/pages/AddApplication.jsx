
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import useApplicationStore from "../stores/applicationStore";
import { toast } from "sonner";

const applicationSchema = z.object({
  company: z.string().min(2, "Company name is required"),
  role: z.string().min(2, "Role is required"),
  status: z.enum(["Applied", "Interview", "Selected", "Rejected"], {
    error: "Please select a valid status",
  }),
  date: z.string().min(1, "Date is required"),
  notes: z.string().min(1, "Notes are required"),
});

function AddApplication() {
  const location = useLocation();

  const [formNote, setFormNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [createdApplication, setCreatedApplication] = useState(null);

  const applications = useApplicationStore(
    (state) => state.applications
  );

  const addApplication = useApplicationStore(
    (state) => state.addApplication
  );

  const pendingApplication = applications.find(
    (application) => application.optimistic
  );

  // Job Search-la irundhu vandha job details
  const trackedJob = location.state?.job;

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(applicationSchema),
    defaultValues: {
      company: "",
      role: "",
      status: "Applied",
      date: new Date().toISOString().split("T")[0],
      notes: "",
    },
  });

  const watchedNotes = watch("notes");

  // =========================
  // Pre-fill form from Job Search
  // =========================
  useEffect(() => {
    if (!trackedJob) {
      return;
    }

    const jobNotes = [
      "Tracked from Job Search",
      trackedJob.salary
        ? `Salary: ${trackedJob.salary}`
        : "",
      trackedJob.link
        ? `Job Link: ${trackedJob.link}`
        : "",
    ]
      .filter(Boolean)
      .join("\n");

    reset({
      company: trackedJob.company || "",
      role: trackedJob.role || "",
      status: "Applied",
      date: new Date().toISOString().split("T")[0],
      notes: jobNotes || "Tracked from Job Search",
    });

    setFormNote(jobNotes || "Tracked from Job Search");
  }, [trackedJob, reset]);

  const onSubmit = async (data) => {
    try {
      setSubmitting(true);
      setSubmitError("");
      setCreatedApplication(null);

      const statusMap = {
        Applied: "APPLIED",
        Interview: "INTERVIEW",
        Selected: "OFFER",
        Rejected: "REJECTED",
      };

      const created = await addApplication({
        company: data.company,
        role: data.role,
        status: statusMap[data.status],
        notes: data.notes,
        applied_date: data.date,
      });

      setCreatedApplication(created);

      toast.success("Application added successfully", {
        description: `${created.company} - ${created.role}`,
      });
    } catch (error) {
      console.error(
        "Failed to create application:",
        error
      );

      setSubmitError(
        "Failed to create application. Please try again."
      );

      toast.error("Failed to add application", {
        description:
          "Please check the form and try again.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <h1>Add Application</h1>

      {trackedJob && (
        <div className="mb-4 rounded-md border p-4">
          <p className="text-sm font-medium">
            Job tracked from Job Search
          </p>

          <p className="text-sm text-muted-foreground">
            {trackedJob.company} - {trackedJob.role}
          </p>
        </div>
      )}

      {submitError && (
        <p className="form-error">
          {submitError}
        </p>
      )}

      {(pendingApplication || createdApplication) && (
        <div>
          <h3>
            {(pendingApplication || createdApplication).company}
          </h3>

          <p>
            {(pendingApplication || createdApplication).role}
          </p>

          <p>
            {(pendingApplication || createdApplication).status}
          </p>

          {pendingApplication && (
            <p>Saving...</p>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Company */}
        <div>
          <label htmlFor="company">
            Company
          </label>

          <input
            id="company"
            type="text"
            {...register("company")}
          />

          {errors.company && (
            <p className="form-error">
              {errors.company.message}
            </p>
          )}
        </div>

        {/* Role */}
        <div>
          <label htmlFor="role">
            Role
          </label>

          <input
            id="role"
            type="text"
            {...register("role")}
          />

          {errors.role && (
            <p className="form-error">
              {errors.role.message}
            </p>
          )}
        </div>

        {/* Status */}
        <div>
          <label htmlFor="status">
            Status
          </label>

          <select
            id="status"
            {...register("status")}
          >
            <option value="">
              Select Status
            </option>

            <option value="Applied">
              Applied
            </option>

            <option value="Interview">
              Interview
            </option>

            <option value="Selected">
              Selected
            </option>

            <option value="Rejected">
              Rejected
            </option>
          </select>

          {errors.status && (
            <p className="form-error">
              {errors.status.message}
            </p>
          )}
        </div>

        {/* Date */}
        <div>
          <label htmlFor="date">
            Date
          </label>

          <input
            id="date"
            type="date"
            {...register("date")}
          />

          {errors.date && (
            <p className="form-error">
              {errors.date.message}
            </p>
          )}
        </div>

        {/* Notes */}
        <div>
          <label htmlFor="notes">
            Notes
          </label>

          <textarea
            id="notes"
            rows="4"
            {...register("notes")}
            onChange={(event) =>
              setFormNote(event.target.value)
            }
          />

          <p>
            Characters:{" "}
            {watchedNotes?.length || formNote.length}
          </p>

          {errors.notes && (
            <p className="form-error">
              {errors.notes.message}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={submitting}
        >
          {submitting
            ? "Adding..."
            : "Add Application"}
        </button>
      </form>
    </div>
  );
}

export default AddApplication;

