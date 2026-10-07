import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "../contexts/AuthContext";
import toast from "react-hot-toast";

const profileSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  timezone: z.string().min(1, "Timezone is required"),
  webhook_url: z.string().url("Invalid URL").optional().or(z.literal("")),
});

const passwordSchema = z.object({
  current_password: z.string().min(1, "Current password required"),
  new_password: z.string().min(8, "Min 8 characters"),
  confirm_password: z.string().min(1, "Confirm your password"),
}).refine((d) => d.new_password === d.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

const deleteSchema = z.object({
  password: z.string().min(1, "Password required"),
});

const TABS = ["profile", "security", "notifications", "danger"];
const TAB_LABELS = { profile: "Profile", security: "Security", notifications: "Notifications", danger: "Danger Zone" };

const TIMEZONES = [
  "UTC", "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
  "Europe/London", "Europe/Paris", "Europe/Berlin",
  "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata", "Asia/Dubai",
  "Australia/Sydney", "Pacific/Auckland",
];

function FieldGroup({ label, hint, children }) {
  return (
    <div>
      <label className="label-gold">{label}</label>
      {children}
      {hint && <p style={{ fontSize: "11px", color: "#555", marginTop: "4px" }}>{hint}</p>}
    </div>
  );
}

function ErrorMsg({ msg }) {
  if (!msg) return null;
  return <p style={{ fontSize: "12px", color: "#ef4444", marginTop: "4px" }}>{msg}</p>;
}

export default function Settings() {
  const { user, getProfile, updateProfile, changePassword, deleteAccount } = useAuth();
  const [tab, setTab] = useState("profile");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    getProfile();
  }, []);

  const {
    register: rProfile,
    handleSubmit: hProfile,
    formState: { errors: eProfile, isSubmitting: sProfile },
  } = useForm({
    resolver: zodResolver(profileSchema),
    defaultValues: { name: user?.name || "", timezone: user?.timezone || "UTC", webhook_url: user?.webhook_url || "" },
  });

  const {
    register: rPassword,
    handleSubmit: hPassword,
    formState: { errors: ePassword, isSubmitting: sPassword },
    reset: resetPassword,
  } = useForm({ resolver: zodResolver(passwordSchema) });

  const {
    register: rDelete,
    handleSubmit: hDelete,
    formState: { errors: eDelete },
  } = useForm({ resolver: zodResolver(deleteSchema) });

  const onProfile = async (data) => {
    try {
      await updateProfile({ name: data.name, timezone: data.timezone, webhook_url: data.webhook_url || undefined });
      toast.success("Profile updated!");
    } catch { toast.error("Failed to update profile"); }
  };

  const onPassword = async (data) => {
    try {
      await changePassword(data.current_password, data.new_password);
      toast.success("Password changed!");
      resetPassword();
    } catch (err) { toast.error(err.response?.data?.error || "Failed to change password"); }
  };

  const onDelete = async (data) => {
    if (!confirmDelete) { toast.error("Please check the confirmation box"); return; }
    try {
      setDeleting(true);
      await deleteAccount(data.password);
      toast.success("Account deleted.");
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to delete account");
    } finally { setDeleting(false); setConfirmDelete(false); }
  };

  const Card = ({ children }) => (
    <div style={{
      background: "#111111", border: "1px solid #1F1F1F",
      borderRadius: "14px", padding: "28px 24px"
    }}>
      {children}
    </div>
  );

  return (
    <div style={{ maxWidth: "680px", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: "26px", fontWeight: 800, color: "#fff", marginBottom: "6px" }}>Settings</h1>
        <p style={{ color: "#777", fontSize: "14px" }}>Manage your account and preferences.</p>
      </div>

      {/* User Overview */}
      <Card>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div style={{
            width: 52, height: 52, borderRadius: "50%",
            background: "linear-gradient(135deg, #D4AF37, #8B7523)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "20px", fontWeight: 800, color: "#050505", flexShrink: 0
          }}>
            {user?.name?.charAt(0)?.toUpperCase() || "U"}
          </div>
          <div>
            <div style={{ fontSize: "16px", fontWeight: 700, color: "#fff" }}>{user?.name}</div>
            <div style={{ fontSize: "13px", color: "#777" }}>{user?.email}</div>
            <div style={{ marginTop: "4px" }}>
              <span style={{
                background: "rgba(255,215,0,0.12)", color: "#D4AF37",
                border: "1px solid rgba(255,215,0,0.25)",
                borderRadius: "100px", fontSize: "10px", fontWeight: 600,
                padding: "2px 10px", textTransform: "uppercase", letterSpacing: "0.06em"
              }}>
                {user?.role || "USER"}
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div style={{
        display: "flex", gap: "2px",
        background: "#111111", border: "1px solid #1F1F1F",
        borderRadius: "10px", padding: "4px"
      }}>
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              flex: 1, padding: "8px 12px", borderRadius: "7px",
              border: "none", cursor: "pointer", fontSize: "13px", fontWeight: 500,
              transition: "all 0.2s",
              background: tab === t ? (t === "danger" ? "rgba(239,68,68,0.15)" : "rgba(255,215,0,0.12)") : "transparent",
              color: tab === t ? (t === "danger" ? "#ef4444" : "#FFD700") : "#777",
            }}
          >
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {tab === "profile" && (
        <Card>
          <h2 style={{ fontSize: "16px", fontWeight: 700, color: "#fff", marginBottom: "4px" }}>Profile Information</h2>
          <p style={{ fontSize: "13px", color: "#777", marginBottom: "24px" }}>Update your basic profile information.</p>

          <form onSubmit={hProfile(onProfile)} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <FieldGroup label="Full Name">
              <input className="input-gold" {...rProfile("name")} placeholder="Your full name" />
              <ErrorMsg msg={eProfile.name?.message} />
            </FieldGroup>

            <FieldGroup label="Email Address">
              <input className="input-gold" value={user?.email || ""} readOnly
                style={{ cursor: "not-allowed", opacity: 0.6 }} />
              <p style={{ fontSize: "11px", color: "#555", marginTop: "4px" }}>Email cannot be changed.</p>
            </FieldGroup>

            <FieldGroup label="Timezone">
              <select className="input-gold" {...rProfile("timezone")}>
                {TIMEZONES.map((tz) => <option key={tz} value={tz}>{tz}</option>)}
              </select>
              <ErrorMsg msg={eProfile.timezone?.message} />
            </FieldGroup>

            <FieldGroup label="Slack Webhook URL (Optional)"
              hint="Enter a Slack webhook URL to receive interview notifications.">
              <input className="input-gold" type="url" placeholder="https://hooks.slack.com/services/..."
                {...rProfile("webhook_url")} />
              <ErrorMsg msg={eProfile.webhook_url?.message} />
            </FieldGroup>

            <button type="submit" className="btn-gold" disabled={sProfile} style={{ alignSelf: "flex-start", padding: "10px 24px" }}>
              {sProfile ? "Saving..." : "Save Changes"}
            </button>
          </form>
        </Card>
      )}

      {/* Security Tab */}
      {tab === "security" && (
        <Card>
          <h2 style={{ fontSize: "16px", fontWeight: 700, color: "#fff", marginBottom: "4px" }}>Change Password</h2>
          <p style={{ fontSize: "13px", color: "#777", marginBottom: "24px" }}>Update your account password.</p>

          <form onSubmit={hPassword(onPassword)} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <FieldGroup label="Current Password">
              <input className="input-gold" type="password" {...rPassword("current_password")} placeholder="••••••••" />
              <ErrorMsg msg={ePassword.current_password?.message} />
            </FieldGroup>

            <FieldGroup label="New Password">
              <input className="input-gold" type="password" {...rPassword("new_password")} placeholder="Min. 8 characters" />
              <ErrorMsg msg={ePassword.new_password?.message} />
            </FieldGroup>

            <FieldGroup label="Confirm New Password">
              <input className="input-gold" type="password" {...rPassword("confirm_password")} placeholder="Repeat password" />
              <ErrorMsg msg={ePassword.confirm_password?.message} />
            </FieldGroup>

            <button type="submit" className="btn-gold" disabled={sPassword} style={{ alignSelf: "flex-start", padding: "10px 24px" }}>
              {sPassword ? "Changing..." : "Change Password"}
            </button>
          </form>
        </Card>
      )}

      {/* Notifications Tab */}
      {tab === "notifications" && (
        <Card>
          <h2 style={{ fontSize: "16px", fontWeight: 700, color: "#fff", marginBottom: "4px" }}>Notification Settings</h2>
          <p style={{ fontSize: "13px", color: "#777", marginBottom: "24px" }}>Configure how you receive notifications.</p>

          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <div style={{
              background: "rgba(255,215,0,0.05)", border: "1px solid rgba(255,215,0,0.15)",
              borderRadius: "10px", padding: "16px"
            }}>
              <div style={{ fontSize: "14px", fontWeight: 600, color: "#FFD700", marginBottom: "6px" }}>
                🔔 Real-time Notifications (Active)
              </div>
              <p style={{ fontSize: "13px", color: "#B8B8B8" }}>
                You receive real-time notifications via Server-Sent Events (SSE) when your application status changes, interviews are scheduled, or other updates occur.
              </p>
            </div>

            <div>
              <label className="label-gold">Slack Webhook URL</label>
              <input
                className="input-gold"
                type="url"
                defaultValue={user?.webhook_url || ""}
                placeholder="https://hooks.slack.com/services/..."
                readOnly
                style={{ cursor: "not-allowed", opacity: 0.6 }}
              />
              <p style={{ fontSize: "11px", color: "#555", marginTop: "4px" }}>Manage your webhook URL in the Profile tab.</p>
            </div>

            <div>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "#fff", marginBottom: "4px" }}>Interview Reminders</div>
              <p style={{ fontSize: "13px", color: "#B8B8B8" }}>
                Email reminders are sent 24 hours before scheduled interviews. Times are shown in {user?.timezone || "UTC"}.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Danger Tab */}
      {tab === "danger" && (
        <Card>
          <h2 style={{ fontSize: "16px", fontWeight: 700, color: "#ef4444", marginBottom: "4px" }}>Delete Account</h2>
          <p style={{ fontSize: "13px", color: "#777", marginBottom: "24px" }}>
            Permanently delete your account and all associated data. This action cannot be undone.
          </p>

          <div style={{
            background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.2)",
            borderRadius: "10px", padding: "16px", marginBottom: "20px"
          }}>
            <div style={{ fontSize: "13px", color: "#ef4444", fontWeight: 600, marginBottom: "4px" }}>⚠ Warning</div>
            <p style={{ fontSize: "13px", color: "#B8B8B8" }}>
              This will delete your account, all applications, and associated data permanently.
            </p>
          </div>

          <form onSubmit={hDelete(onDelete)} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <FieldGroup label="Enter your password to confirm">
              <input className="input-gold" type="password" {...rDelete("password")} placeholder="••••••••" />
              <ErrorMsg msg={eDelete.password?.message} />
            </FieldGroup>

            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <input
                type="checkbox"
                id="confirm-delete"
                checked={confirmDelete}
                onChange={(e) => setConfirmDelete(e.target.checked)}
                style={{ width: 16, height: 16, cursor: "pointer", accentColor: "#ef4444" }}
              />
              <label htmlFor="confirm-delete" style={{ fontSize: "13px", color: "#B8B8B8", cursor: "pointer" }}>
                I understand this will permanently delete my account and all data
              </label>
            </div>

            <button
              type="submit"
              className="btn-danger"
              disabled={deleting || !confirmDelete}
              style={{ alignSelf: "flex-start", padding: "10px 24px" }}
            >
              {deleting ? "Deleting..." : "Delete Account"}
            </button>
          </form>
        </Card>
      )}
    </div>
  );
}