import React, { useState, useEffect } from "react";
import api from "../services/api";
import toast from "react-hot-toast";

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const STATUS_BADGES = {
  APPLIED: { label: "Applied", color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200" },
  UNDER_REVIEW: { label: "Under Review", color: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200" },
  PHONE_SCREEN: { label: "Phone Screen", color: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200" },
  INTERVIEW: { label: "Interview", color: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200" },
  OFFER: { label: "Offer", color: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200" },
  REJECTED: { label: "Rejected", color: "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200" },
  WITHDRAWN: { label: "Withdrawn", color: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300" },
};

export default function HRDashboard() {
  const [applications, setApplications] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedApp, setSelectedApp] = useState(null);

  // Modals state
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [interviewModalOpen, setInterviewModalOpen] = useState(false);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);

  // Form states
  const [newStatus, setNewStatus] = useState("");
  const [statusNotes, setStatusNotes] = useState("");

  const [interviewDate, setInterviewDate] = useState("");
  const [interviewTime, setInterviewTime] = useState("");
  const [interviewRound, setInterviewRound] = useState("Technical Round 1");
  const [interviewType, setInterviewType] = useState("Online");
  const [meetingLink, setMeetingLink] = useState("");
  const [interviewer, setInterviewer] = useState("");
  const [hrNotes, setHrNotes] = useState("");

  const [techSkills, setTechSkills] = useState("Good");
  const [commSkills, setCommSkills] = useState("Good");
  const [overallFeedback, setOverallFeedback] = useState("");
  const [recommendation, setRecommendation] = useState("Hire");
  const [internalFeedbackNotes, setInternalFeedbackNotes] = useState("");

  const fetchHRApplications = async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();
      if (search) queryParams.set("search", search);
      if (statusFilter) queryParams.set("status", statusFilter);

      const res = await api.get(`/api/hr/applications?${queryParams.toString()}`);
      setApplications(res.data.applications || []);
      setStats(res.data.stats || {});
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to fetch HR applications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHRApplications();
  }, [search, statusFilter]);

  const fetchFullDetail = async (appId) => {
    try {
      const res = await api.get(`/api/hr/applications/${appId}`);
      setSelectedApp(res.data);
      setDetailModalOpen(true);
    } catch (err) {
      toast.error("Failed to load application details");
    }
  };

  const handleUpdateStatus = async (e) => {
    e.preventDefault();
    if (!selectedApp || !newStatus) return;

    try {
      await api.patch(`/api/hr/applications/${selectedApp.id}/status`, {
        status: newStatus,
        notes: statusNotes,
      });
      toast.success(`Status updated to ${newStatus}`);
      setStatusModalOpen(false);
      fetchHRApplications();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to update status");
    }
  };

  const handleScheduleInterview = async (e) => {
    e.preventDefault();
    if (!selectedApp) return;

    try {
      await api.patch(`/api/hr/applications/${selectedApp.id}/interview`, {
        interview_date: interviewDate || null,
        interview_time: interviewTime || null,
        interview_round: interviewRound,
        interview_type: interviewType,
        meeting_link: meetingLink,
        interviewer: interviewer,
        hr_notes: hrNotes,
      });
      toast.success("Interview scheduled & notification sent to candidate");
      setInterviewModalOpen(false);
      fetchHRApplications();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to schedule interview");
    }
  };

  const handleSubmitFeedback = async (e) => {
    e.preventDefault();
    if (!selectedApp) return;

    try {
      await api.post(`/api/hr/applications/${selectedApp.id}/feedback`, {
        technical_skills: techSkills,
        communication: commSkills,
        overall_feedback: overallFeedback,
        recommendation: recommendation,
        internal_notes: internalFeedbackNotes,
      });
      toast.success("Interview feedback recorded");
      setFeedbackModalOpen(false);
      fetchHRApplications();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to submit feedback");
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">HR Recruitment Portal</h1>
          <p className="text-muted-foreground">Manage job applications, schedule interviews, and track candidate progression.</p>
        </div>
      </div>

      {/* Stats Header */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {Object.entries(STATUS_BADGES).map(([key, info]) => (
          <Card key={key} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setStatusFilter(statusFilter === key ? "" : key)}>
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{info.label}</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div className="text-2xl font-bold">{stats[key] || 0}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-card p-4 rounded-lg border shadow-sm">
        <input
          type="text"
          placeholder="Search company, candidate, role..."
          className="w-full sm:w-80 px-3 py-2 border rounded-md text-sm bg-background"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="flex items-center gap-2">
          <select
            className="px-3 py-2 border rounded-md text-sm bg-background"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            {Object.entries(STATUS_BADGES).map(([key, info]) => (
              <option key={key} value={key}>{info.label}</option>
            ))}
          </select>
          {statusFilter && (
            <Button variant="ghost" size="sm" onClick={() => setStatusFilter("")}>
              Clear Filter
            </Button>
          )}
        </div>
      </div>

      {/* Applications Table */}
      <div className="border rounded-lg bg-card shadow-sm overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted/50 border-b">
            <tr>
              <th className="p-3 font-semibold">Candidate</th>
              <th className="p-3 font-semibold">Role & Company</th>
              <th className="p-3 font-semibold">Applied Date</th>
              <th className="p-3 font-semibold">Current Status</th>
              <th className="p-3 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr>
                <td colSpan={5} className="p-6 text-center text-muted-foreground">Loading applications...</td>
              </tr>
            ) : applications.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-6 text-center text-muted-foreground">No applications found matching criteria.</td>
              </tr>
            ) : (
              applications.map((app) => {
                const badge = STATUS_BADGES[app.status] || { label: app.status, color: "bg-gray-100" };
                return (
                  <tr key={app.id} className="hover:bg-muted/30">
                    <td className="p-3">
                      <div className="font-medium">{app.candidate?.name || "Candidate"}</div>
                      <div className="text-xs text-muted-foreground">{app.candidate?.email}</div>
                    </td>
                    <td className="p-3">
                      <div className="font-medium">{app.role}</div>
                      <div className="text-xs text-muted-foreground">{app.company}</div>
                    </td>
                    <td className="p-3 text-muted-foreground">
                      {app.applied_date ? new Date(app.applied_date).toLocaleDateString() : "N/A"}
                    </td>
                    <td className="p-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.color}`}>
                        {badge.label}
                      </span>
                    </td>
                    <td className="p-3 text-right space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedApp(app);
                          setNewStatus(app.status);
                          setStatusModalOpen(true);
                        }}
                      >
                        Status
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedApp(app);
                          setInterviewModalOpen(true);
                        }}
                      >
                        Interview
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedApp(app);
                          setFeedbackModalOpen(true);
                        }}
                      >
                        Feedback
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => fetchFullDetail(app.id)}
                      >
                        Timeline
                      </Button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Status Update Modal */}
      <Dialog open={statusModalOpen} onOpenChange={setStatusModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Status - {selectedApp?.role} ({selectedApp?.company})</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpdateStatus} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">New Status</label>
              <select
                className="w-full p-2 border rounded bg-background"
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                required
              >
                {Object.entries(STATUS_BADGES).map(([key, info]) => (
                  <option key={key} value={key}>{info.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Notes (Optional)</label>
              <textarea
                className="w-full p-2 border rounded bg-background"
                rows={3}
                placeholder="Reason or notes for status update..."
                value={statusNotes}
                onChange={(e) => setStatusNotes(e.target.value)}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => setStatusModalOpen(false)}>Cancel</Button>
              <Button type="submit">Save & Notify Candidate</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Schedule Interview Modal */}
      <Dialog open={interviewModalOpen} onOpenChange={setInterviewModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Schedule Interview - {selectedApp?.candidate?.name}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleScheduleInterview} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Interview Date</label>
                <input
                  type="date"
                  className="w-full p-2 border rounded bg-background"
                  value={interviewDate}
                  onChange={(e) => setInterviewDate(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Interview Time</label>
                <input
                  type="time"
                  className="w-full p-2 border rounded bg-background"
                  value={interviewTime}
                  onChange={(e) => setInterviewTime(e.target.value)}
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Round Name</label>
                <input
                  type="text"
                  className="w-full p-2 border rounded bg-background"
                  value={interviewRound}
                  onChange={(e) => setInterviewRound(e.target.value)}
                  placeholder="e.g. Technical Round 1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Type</label>
                <select
                  className="w-full p-2 border rounded bg-background"
                  value={interviewType}
                  onChange={(e) => setInterviewType(e.target.value)}
                >
                  <option value="Online">Online Video Call</option>
                  <option value="Phone Screen">Phone Screen</option>
                  <option value="In-person">In-person</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Meeting Link</label>
              <input
                type="url"
                className="w-full p-2 border rounded bg-background"
                placeholder="https://meet.google.com/..."
                value={meetingLink}
                onChange={(e) => setMeetingLink(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Interviewer Name</label>
              <input
                type="text"
                className="w-full p-2 border rounded bg-background"
                placeholder="e.g. John Doe (Engineering Lead)"
                value={interviewer}
                onChange={(e) => setInterviewer(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">HR Internal Preparation Notes</label>
              <textarea
                className="w-full p-2 border rounded bg-background"
                rows={2}
                placeholder="Private notes (not visible to candidate)..."
                value={hrNotes}
                onChange={(e) => setHrNotes(e.target.value)}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => setInterviewModalOpen(false)}>Cancel</Button>
              <Button type="submit">Schedule & Notify Candidate</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Feedback Modal */}
      <Dialog open={feedbackModalOpen} onOpenChange={setFeedbackModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Interview Feedback - {selectedApp?.candidate?.name}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmitFeedback} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Technical Rating</label>
                <select className="w-full p-2 border rounded bg-background" value={techSkills} onChange={(e) => setTechSkills(e.target.value)}>
                  <option value="Excellent">Excellent</option>
                  <option value="Good">Good</option>
                  <option value="Average">Average</option>
                  <option value="Below Average">Below Average</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Communication</label>
                <select className="w-full p-2 border rounded bg-background" value={commSkills} onChange={(e) => setCommSkills(e.target.value)}>
                  <option value="Excellent">Excellent</option>
                  <option value="Good">Good</option>
                  <option value="Average">Average</option>
                  <option value="Needs Improvement">Needs Improvement</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Recommendation</label>
              <select className="w-full p-2 border rounded bg-background" value={recommendation} onChange={(e) => setRecommendation(e.target.value)}>
                <option value="Hire">Hire</option>
                <option value="Maybe">Maybe</option>
                <option value="No Hire">No Hire</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Overall Feedback</label>
              <textarea
                className="w-full p-2 border rounded bg-background"
                rows={3}
                placeholder="Detailed candidate evaluation..."
                value={overallFeedback}
                onChange={(e) => setOverallFeedback(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Internal Notes (HR only)</label>
              <textarea
                className="w-full p-2 border rounded bg-background"
                rows={2}
                placeholder="Compensation, start date discussions..."
                value={internalFeedbackNotes}
                onChange={(e) => setInternalFeedbackNotes(e.target.value)}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => setFeedbackModalOpen(false)}>Cancel</Button>
              <Button type="submit">Submit Feedback</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Full Detail / Timeline Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Application History Timeline - {selectedApp?.role} at {selectedApp?.company}</DialogTitle>
          </DialogHeader>

          {selectedApp && (
            <div className="space-y-6 text-sm">
              <div className="grid grid-cols-2 gap-4 bg-muted/30 p-4 rounded-lg">
                <div>
                  <span className="font-semibold block text-xs text-muted-foreground">CANDIDATE</span>
                  <div className="font-medium text-base">{selectedApp.candidate?.name}</div>
                  <div className="text-muted-foreground">{selectedApp.candidate?.email}</div>
                </div>
                <div>
                  <span className="font-semibold block text-xs text-muted-foreground">CURRENT STATUS</span>
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold mt-1 ${(STATUS_BADGES[selectedApp.status] || {}).color}`}>
                    {selectedApp.status}
                  </span>
                </div>
              </div>

              {selectedApp.interview_details && (
                <div className="border border-amber-200 bg-amber-50 dark:bg-amber-950/30 p-4 rounded-lg space-y-2">
                  <h4 className="font-semibold text-amber-900 dark:text-amber-200">Scheduled Interview</h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div><span className="font-medium">Round:</span> {selectedApp.interview_details.interview_round}</div>
                    <div><span className="font-medium">Type:</span> {selectedApp.interview_details.interview_type}</div>
                    <div><span className="font-medium">Date:</span> {selectedApp.interview_details.interview_date}</div>
                    <div><span className="font-medium">Time:</span> {selectedApp.interview_details.interview_time}</div>
                    {selectedApp.interview_details.meeting_link && (
                      <div className="col-span-2">
                        <span className="font-medium">Link:</span>{" "}
                        <a href={selectedApp.interview_details.meeting_link} target="_blank" rel="noreferrer" className="text-blue-600 underline">
                          {selectedApp.interview_details.meeting_link}
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div>
                <h4 className="font-semibold text-base mb-3">Status History Timeline</h4>
                {selectedApp.status_history && selectedApp.status_history.length > 0 ? (
                  <div className="relative border-l border-muted pl-6 space-y-6">
                    {selectedApp.status_history.map((hist, idx) => (
                      <div key={hist.id || idx} className="relative">
                        <div className="absolute -left-[31px] top-1 w-3 h-3 rounded-full bg-primary" />
                        <div className="font-semibold text-sm">
                          {hist.old_status ? `${hist.old_status} ➔ ${hist.new_status}` : `Application Created (${hist.new_status})`}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {new Date(hist.changed_at).toLocaleString()} {hist.changed_by_name ? `by ${hist.changed_by_name}` : ""}
                        </div>
                        {hist.notes && (
                          <div className="text-xs bg-muted/40 p-2 rounded mt-1 italic">{hist.notes}</div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-xs">No status history recorded yet.</p>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
