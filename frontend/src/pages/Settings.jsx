import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "../contexts/AuthContext";
import toast from "react-hot-toast";
import { Button } from "../components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/card";

const profileSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  timezone: z.string().min(1, "Timezone is required"),
  webhook_url: z.string().url("Invalid URL format").optional().or(z.literal("")),
});

const passwordSchema = z.object({
  current_password: z.string().min(1, "Current password is required"),
  new_password: z.string().min(8, "New password must be at least 8 characters"),
  confirm_password: z.string().min(1, "Please confirm your new password"),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

const deleteAccountSchema = z.object({
  password: z.string().min(1, "Password is required"),
});

const commonTimezones = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Tokyo",
  "Asia/Shanghai",
  "Asia/Kolkata",
  "Asia/Dubai",
  "Australia/Sydney",
  "Pacific/Auckland",
];

function Settings() {
  const { user, getProfile, updateProfile, changePassword, deleteAccount } = useAuth();
  const [activeTab, setActiveTab] = useState("profile");
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const {
    register: registerProfile,
    handleSubmit: handleSubmitProfile,
    formState: { errors: profileErrors, isSubmitting: profileSubmitting },
  } = useForm({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: user?.name || "",
      timezone: user?.timezone || "UTC",
      webhook_url: user?.webhook_url || "",
    },
  });

  const {
    register: registerPassword,
    handleSubmit: handleSubmitPassword,
    formState: { errors: passwordErrors, isSubmitting: passwordSubmitting },
    reset: resetPassword,
  } = useForm({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  });

  const {
    register: registerDelete,
    handleSubmit: handleSubmitDelete,
    formState: { errors: deleteErrors },
  } = useForm({
    resolver: zodResolver(deleteAccountSchema),
    defaultValues: {
      password: "",
    },
  });

  useEffect(() => {
    getProfile();
  }, [getProfile]);

  const onSubmitProfile = async (data) => {
    try {
      await updateProfile({
        name: data.name,
        timezone: data.timezone,
        webhook_url: data.webhook_url || undefined,
      });
      toast.success("Profile updated successfully!");
    } catch (error) {
      console.error("Failed to update profile:", error);
      toast.error("Failed to update profile");
    }
  };

  const onSubmitPassword = async (data) => {
    try {
      await changePassword(data.current_password, data.new_password);
      toast.success("Password changed successfully!");
      resetPassword();
    } catch (error) {
      console.error("Failed to change password:", error);
      toast.error(error.response?.data?.error || "Failed to change password");
    }
  };

  const onSubmitDelete = async (data) => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      toast.error("Please confirm by checking the box and clicking again");
      return;
    }
    try {
      setDeleting(true);
      await deleteAccount(data.password);
      toast.success("Account deleted successfully!");
    } catch (error) {
      console.error("Failed to delete account:", error);
      toast.error(error.response?.data?.error || "Failed to delete account");
    } finally {
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>

      <div className="flex border-b mb-6">
        {["profile", "security", "notifications", "danger"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {activeTab === "profile" && (
        <Card>
          <CardHeader>
            <CardTitle>Profile Information</CardTitle>
            <CardDescription>
              Update your basic profile information
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmitProfile(onSubmitProfile)} className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium mb-1">
                  Name
                </label>
                <input
                  id="name"
                  type="text"
                  {...registerProfile("name")}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
                {profileErrors.name && (
                  <p className="text-sm text-destructive mt-1">{profileErrors.name.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="timezone" className="block text-sm font-medium mb-1">
                  Timezone
                </label>
                <select
                  id="timezone"
                  {...registerProfile("timezone")}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {commonTimezones.map((tz) => (
                    <option key={tz} value={tz}>
                      {tz}
                    </option>
                  ))}
                </select>
                {profileErrors.timezone && (
                  <p className="text-sm text-destructive mt-1">{profileErrors.timezone.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="webhook_url" className="block text-sm font-medium mb-1">
                  Slack Webhook URL (optional)
                </label>
                <input
                  id="webhook_url"
                  type="url"
                  placeholder="https://hooks.slack.com/services/..."
                  {...registerProfile("webhook_url")}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <p className="text-sm text-muted-foreground mt-1">
                  Enter a Slack webhook URL to receive interview notifications
                </p>
                {profileErrors.webhook_url && (
                  <p className="text-sm text-destructive mt-1">{profileErrors.webhook_url.message}</p>
                )}
              </div>

              <Button type="submit" disabled={profileSubmitting}>
                {profileSubmitting ? "Saving..." : "Save Changes"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {activeTab === "security" && (
        <Card>
          <CardHeader>
            <CardTitle>Change Password</CardTitle>
            <CardDescription>
              Update your account password
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmitPassword(onSubmitPassword)} className="space-y-4">
              <div>
                <label htmlFor="current_password" className="block text-sm font-medium mb-1">
                  Current Password
                </label>
                <input
                  id="current_password"
                  type="password"
                  {...registerPassword("current_password")}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
                {passwordErrors.current_password && (
                  <p className="text-sm text-destructive mt-1">{passwordErrors.current_password.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="new_password" className="block text-sm font-medium mb-1">
                  New Password
                </label>
                <input
                  id="new_password"
                  type="password"
                  {...registerPassword("new_password")}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
                {passwordErrors.new_password && (
                  <p className="text-sm text-destructive mt-1">{passwordErrors.new_password.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="confirm_password" className="block text-sm font-medium mb-1">
                  Confirm New Password
                </label>
                <input
                  id="confirm_password"
                  type="password"
                  {...registerPassword("confirm_password")}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
                {passwordErrors.confirm_password && (
                  <p className="text-sm text-destructive mt-1">{passwordErrors.confirm_password.message}</p>
                )}
              </div>

              <Button type="submit" disabled={passwordSubmitting}>
                {passwordSubmitting ? "Changing..." : "Change Password"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {activeTab === "notifications" && (
        <Card>
          <CardHeader>
            <CardTitle>Notification Settings</CardTitle>
            <CardDescription>
              Configure how you receive notifications
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Slack Webhook URL
                </label>
                <input
                  type="url"
                  placeholder="https://hooks.slack.com/services/..."
                  defaultValue={user?.webhook_url || ""}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  readOnly
                />
                <p className="text-sm text-muted-foreground mt-1">
                  Manage your webhook URL in the Profile tab
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Interview Reminders
                </label>
                <p className="text-sm text-muted-foreground">
                  Email reminders are sent 24 hours before scheduled interviews.
                  Times are displayed in your configured timezone ({user?.timezone || "UTC"}).
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "danger" && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Delete Account</CardTitle>
            <CardDescription>
              Permanently delete your account and all associated data. This action cannot be undone.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmitDelete(onSubmitDelete)} className="space-y-4">
              <div>
                <label htmlFor="delete_password" className="block text-sm font-medium mb-1">
                  Enter your password to confirm
                </label>
                <input
                  id="delete_password"
                  type="password"
                  {...registerDelete("password")}
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
                {deleteErrors.password && (
                  <p className="text-sm text-destructive mt-1">{deleteErrors.password.message}</p>
                )}
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="confirm_delete"
                  checked={confirmDelete}
                  onChange={(e) => setConfirmDelete(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <label htmlFor="confirm_delete" className="text-sm">
                  I understand this will permanently delete my account and all data
                </label>
              </div>

              <Button
                type="submit"
                variant="destructive"
                disabled={deleting || !confirmDelete}
              >
                {deleting ? "Deleting..." : "Delete Account"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default Settings;