
import toast from "react-hot-toast";

import { useEffect, useState } from "react";

import { useSearchParams } from "react-router-dom";

import { useDropzone } from "react-dropzone";

import axios from "axios";

import {
  createPaginatedRowModel,
  createSortedRowModel,
  rowPaginationFeature,
  rowSelectionFeature,
  rowSortingFeature,
  tableFeatures,
  useTable,
} from "@tanstack/react-table";

import useApplicationStore from "../stores/applicationStore";

import api from "../services/api";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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

const features = tableFeatures({
  rowSortingFeature,
  rowSelectionFeature,
  rowPaginationFeature,
  sortedRowModel: createSortedRowModel(),
  paginatedRowModel: createPaginatedRowModel(),
});

// --------------------------------------------------
// File Size Formatter
// --------------------------------------------------

const formatFileSize = (bytes) => {
  if (!bytes) {
    return "0 Bytes";
  }

  const units = ["Bytes", "KB", "MB", "GB"];

  const index = Math.floor(
    Math.log(bytes) / Math.log(1024)
  );

  return `${(
    bytes / Math.pow(1024, index)
  ).toFixed(2)} ${units[index]}`;
};

// --------------------------------------------------
// Resume Upload Cell
// --------------------------------------------------

function ResumeCell({ application }) {
  const fetchApplications = useApplicationStore(
    (state) => state.fetchApplications
  );

  const [resumeFile, setResumeFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const [resumeExists, setResumeExists] = useState(
    Boolean(application.resume_path)
  );

  // --------------------------------------------------
  // Sync resume state with backend application data
  // --------------------------------------------------

  useEffect(() => {
    const hasResume = Boolean(application.resume_path);

    setResumeExists(hasResume);

    if (!hasResume) {
      setResumeFile(null);
      setUploadProgress(0);
    }
  }, [application.resume_path]);

  // --------------------------------------------------
  // Upload Resume
  // --------------------------------------------------

  const uploadResume = async (file) => {
    if (!file) {
      return;
    }

    setError("");
    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();

    formData.append("resume", file);

    try {
      await api.post(
        `/api/applications/${application.id}/resume`,
        formData,
        {
          onUploadProgress: (progressEvent) => {
            if (!progressEvent.total) {
              return;
            }

            const progress = Math.round(
              (progressEvent.loaded * 100) /
                progressEvent.total
            );

            setUploadProgress(progress);
          },
        }
      );

      setResumeFile(file);
      setResumeExists(true);
      setUploadProgress(100);

      toast.success(
        "Resume uploaded successfully!"
      );

      // Refresh application data from backend
      await fetchApplications();
    } catch (uploadError) {
      console.error(
        "Resume upload failed:",
        uploadError
      );

      if (
        axios.isAxiosError(uploadError) &&
        uploadError.response?.data?.error
      ) {
        setError(
          uploadError.response.data.error
        );
      } else {
        setError(
          "Resume upload failed. Please try again."
        );
      }

      toast.error(
        "Resume upload failed."
      );

      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  // --------------------------------------------------
  // Dropzone
  // --------------------------------------------------

  const {
    getRootProps,
    getInputProps,
    isDragActive,
  } = useDropzone({
    accept: {
      "application/pdf": [".pdf"],
    },

    multiple: false,

    disabled: uploading,

    onDropRejected: () => {
      setError("Only PDF files are allowed.");

      toast.error(
        "Only PDF files are allowed."
      );
    },

    onDrop: (acceptedFiles) => {
      setError("");

      const file = acceptedFiles[0];

      if (!file) {
        return;
      }

      uploadResume(file);
    },
  });

  // --------------------------------------------------
  // Delete Resume
  // --------------------------------------------------

  const handleDeleteResume = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this resume?"
    );

    if (!confirmed) {
      return;
    }

    setError("");

    try {
      await api.delete(
        `/api/applications/${application.id}/resume`
      );

      // Immediately clear local UI
      setResumeFile(null);
      setResumeExists(false);
      setUploadProgress(0);

      toast.success(
        "Resume deleted successfully!"
      );

      // Re-fetch applications from backend
      // so the latest resume_path is loaded.
      await fetchApplications();
    } catch (deleteError) {
      console.error(
        "Resume delete failed:",
        deleteError
      );

      if (
        axios.isAxiosError(deleteError) &&
        deleteError.response?.data?.error
      ) {
        setError(
          deleteError.response.data.error
        );
      } else {
        setError(
          "Resume delete failed. Please try again."
        );
      }

      toast.error(
        "Resume delete failed."
      );
    }
  };

  // --------------------------------------------------
  // Resume Display
  // --------------------------------------------------

  const displayedFilename =
    resumeFile?.name ||
    (application.resume_path
      ? application.resume_path
          .split(/[\\/]/)
          .pop()
      : "");

  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (
    <div className="min-w-[240px] space-y-3">

      {/* Upload Area */}

      {!resumeExists && !uploading && (
        <div
          {...getRootProps()}
          className={`cursor-pointer rounded-md border-2 border-dashed p-4 text-center transition ${
            isDragActive
              ? "border-primary bg-muted"
              : "border-muted-foreground/30 hover:border-primary"
          }`}
        >
          <input {...getInputProps()} />

          <p className="text-sm font-medium">
            {isDragActive
              ? "Drop PDF here"
              : "Drag & drop PDF"}
          </p>

          <p className="mt-1 text-xs text-muted-foreground">
            or click to select
          </p>
        </div>
      )}

      {/* Upload Progress */}

      {uploading && (
        <div className="space-y-2">
          <p className="text-sm font-medium">
            Uploading resume...
          </p>

          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full bg-primary transition-all"
              style={{
                width: `${uploadProgress}%`,
              }}
            />
          </div>

          <p className="text-xs text-muted-foreground">
            {uploadProgress}%
          </p>
        </div>
      )}

      {/* Uploaded Resume */}

      {resumeExists && !uploading && (
        <div className="space-y-2">

          <div className="rounded-md border p-3">
            <p className="truncate text-sm font-medium">
              {displayedFilename ||
                "Resume uploaded"}
            </p>

            {resumeFile && (
              <p className="mt-1 text-xs text-muted-foreground">
                {formatFileSize(
                  resumeFile.size
                )}
              </p>
            )}
          </div>

          <div className="flex gap-2">

            {/* Replace PDF */}

            <div
              {...getRootProps()}
              className="flex-1 cursor-pointer rounded-md border px-3 py-2 text-center text-xs font-medium hover:bg-muted"
            >
              <input {...getInputProps()} />
              Replace PDF
            </div>

            {/* Delete */}

            <button
              type="button"
              onClick={handleDeleteResume}
              className="rounded-md border px-3 py-2 text-xs font-medium text-destructive hover:bg-destructive/10"
            >
              Delete
            </button>

          </div>
        </div>
      )}

      {/* Error */}

      {error && (
        <p className="text-xs text-destructive">
          {error}
        </p>
      )}

    </div>
  );
}

// --------------------------------------------------
// CSV Export
// --------------------------------------------------

const exportApplicationsToCSV = (
  applications
) => {
  const headers = [
    "Company",
    "Role",
    "Status",
    "Applied Date",
    "Notes",
  ];

  const rows = applications.map(
    (application) => [
      application.company,
      application.role,
      application.status,
      application.applied_date,
      application.notes,
    ]
  );

  const csvContent = [
    headers,
    ...rows,
  ]
    .map((row) =>
      row
        .map((value) => {
          const text = value ?? "";

          return `"${String(text).replace(
            /"/g,
            '""'
          )}"`;
        })
        .join(",")
    )
    .join("\n");

  const blob = new Blob([csvContent], {
    type: "text/csv;charset=utf-8;",
  });

  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = url;
  link.download = "applications.csv";

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(url);
};

// --------------------------------------------------
// Table Columns
// --------------------------------------------------

const columns = [
  {
    accessorKey: "company",
    header: "Company",
  },

  {
    accessorKey: "role",
    header: "Role",
  },

  {
    accessorKey: "status",
    header: "Status",
    enableSorting: false,
    cell: ({ row }) => {
      const application = row.original;
      const badge = STATUS_BADGES[application.status] || {
        label: application.status,
        color: "bg-gray-100 text-gray-800",
      };

      return (
        <span
          className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${badge.color}`}
        >
          {badge.label}
        </span>
      );
    },
  },

  {
    accessorKey: "applied_date",
    header: "Applied Date",
  },

  {
    accessorKey: "notes",
    header: "Notes",
  },

  {
    id: "resume",
    header: "Resume",
    enableSorting: false,

    cell: ({ row }) => (
      <ResumeCell
        application={row.original}
      />
    ),
  },

  {
    id: "actions",
    header: "Action",
    enableSorting: false,
    cell: ({ row }) => (
      <Button
        size="sm"
        variant="outline"
        onClick={() => {
          window.dispatchEvent(
            new CustomEvent("open-candidate-app-detail", {
              detail: row.original,
            })
          );
        }}
      >
        View Details
      </Button>
    ),
  },
];

// --------------------------------------------------
// Applications Page
// --------------------------------------------------

function Applications() {
  const [searchParams, setSearchParams] =
    useSearchParams();

  const applications = useApplicationStore(
    (state) => state.applications
  );

  const loading = useApplicationStore(
    (state) => state.loading
  );

  const error = useApplicationStore(
    (state) => state.error
  );

  const filters = useApplicationStore(
    (state) => state.filters
  );

  const pagination = useApplicationStore(
    (state) => state.pagination
  );

  const fetchApplications = useApplicationStore(
    (state) => state.fetchApplications
  );

  const setStatusFilter = useApplicationStore(
    (state) => state.setStatusFilter
  );

  const setSearchFilter = useApplicationStore(
    (state) => state.setSearchFilter
  );

  const setSort = useApplicationStore(
    (state) => state.setSort
  );

  const setPage = useApplicationStore(
    (state) => state.setPage
  );

  const [selectedApp, setSelectedApp] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    const handler = async (e) => {
      const appItem = e.detail;
      setDetailModalOpen(true);
      setLoadingDetail(true);
      try {
        const res = await api.get(`/api/applications/${appItem.id}`);
        setSelectedApp(res.data);
      } catch (err) {
        setSelectedApp(appItem);
      } finally {
        setLoadingDetail(false);
      }
    };

    window.addEventListener("open-candidate-app-detail", handler);
    return () => window.removeEventListener("open-candidate-app-detail", handler);
  }, []);

  const handleWithdraw = async (appId) => {
    try {
      await api.put(`/api/applications/${appId}`, { status: "WITHDRAWN" });
      toast.success("Application withdrawn successfully");
      setDetailModalOpen(false);
      fetchApplications();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to withdraw application");
    }
  };

  // --------------------------------------------------
  // Read filters and page from URL
  // --------------------------------------------------

  useEffect(() => {
    const statusFromUrl =
      searchParams.get("status") || "";

    const searchFromUrl =
      searchParams.get("search") || "";

    const sortFromUrl =
      searchParams.get("sort") || "newest";

    const pageFromUrl =
      Number(searchParams.get("page")) || 1;

    if (statusFromUrl !== filters.status) {
      setStatusFilter(statusFromUrl);
    }

    if (searchFromUrl !== filters.search) {
      setSearchFilter(searchFromUrl);
    }

    if (sortFromUrl !== filters.sort) {
      setSort(sortFromUrl);
    }

    if (pageFromUrl !== pagination.page) {
      setPage(pageFromUrl);
    }
  }, []);

  // --------------------------------------------------
  // Fetch Applications
  // --------------------------------------------------

  useEffect(() => {
    fetchApplications();
  }, [
    fetchApplications,
    filters.status,
    filters.search,
    filters.sort,
    pagination.page,
  ]);

  // --------------------------------------------------
  // Status Filter
  // --------------------------------------------------

  const handleStatusChange = (value) => {
    const status =
      value === "ALL" ? "" : value;

    setStatusFilter(status);

    const nextParams =
      new URLSearchParams(searchParams);

    if (status) {
      nextParams.set(
        "status",
        status
      );
    } else {
      nextParams.delete("status");
    }

    nextParams.delete("page");

    setSearchParams(nextParams);
  };

  // --------------------------------------------------
  // Search Filter
  // --------------------------------------------------

  const handleSearchChange = (event) => {
    const search = event.target.value;

    setSearchFilter(search);

    const nextParams = new URLSearchParams(searchParams);

    if (search) {
      nextParams.set("search", search);
    } else {
      nextParams.delete("search");
    }

    nextParams.delete("page");

    setSearchParams(nextParams);
  };

  // --------------------------------------------------
  // Sort
  // --------------------------------------------------

  const handleSortChange = (value) => {
    setSort(value);

    const nextParams =
      new URLSearchParams(searchParams);

    if (
      value &&
      value !== "newest"
    ) {
      nextParams.set(
        "sort",
        value
      );
    } else {
      nextParams.delete("sort");
    }

    nextParams.delete("page");

    setSearchParams(nextParams);
  };

  // --------------------------------------------------
  // Pagination
  // --------------------------------------------------

  const handlePageChange = (page) => {
    const totalPages =
      pagination.pages || 1;

    const requestedPage =
      Number(page) || 1;

    const nextPage = Math.min(
      Math.max(
        requestedPage,
        1
      ),
      totalPages
    );

    setPage(nextPage);

    const nextParams =
      new URLSearchParams(searchParams);

    if (filters.status) {
      nextParams.set(
        "status",
        filters.status
      );
    } else {
      nextParams.delete("status");
    }

    if (filters.search) {
      nextParams.set(
        "search",
        filters.search
      );
    } else {
      nextParams.delete("search");
    }

    if (
      filters.sort &&
      filters.sort !== "newest"
    ) {
      nextParams.set(
        "sort",
        filters.sort
      );
    } else {
      nextParams.delete("sort");
    }

    if (nextPage > 1) {
      nextParams.set(
        "page",
        String(nextPage)
      );
    } else {
      nextParams.delete("page");
    }

    setSearchParams(nextParams);
  };

  // --------------------------------------------------
  // TanStack Table
  // --------------------------------------------------

  const table = useTable({
    key: "applications-table",
    features,
    data: applications,
    columns,

    initialState: {
      pagination: {
        pageIndex: 0,
        pageSize: 10,
      },
    },
  });

  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (
    <div className="space-y-6">

      {/* Page Header */}

      <div>
        <h1 className="text-2xl font-bold">
          Applications
        </h1>

        <p className="text-sm text-muted-foreground">
          Manage, search and sort your job applications.
        </p>
      </div>

      {/* Search and Filters */}

      <div className="flex flex-col gap-4 md:flex-row md:items-end">

        {/* Search */}

        <div className="flex-1">
          <label
            htmlFor="search-filter"
            className="mb-2 block text-sm font-medium"
          >
            Search
          </label>

          <input
            id="search-filter"
            type="text"
            value={filters.search}
            placeholder="Search company or role"
            onChange={handleSearchChange}
            className="w-full rounded-md border px-3 py-2"
          />
        </div>

        {/* Sort */}

        <div>
          <label
            htmlFor="sort-filter"
            className="mb-2 block text-sm font-medium"
          >
            Sort
          </label>

          <Select
            value={filters.sort}
            onValueChange={handleSortChange}
          >
            <SelectTrigger
              id="sort-filter"
              className="w-full md:w-[200px]"
            >
              <SelectValue placeholder="Sort applications" />
            </SelectTrigger>

            <SelectContent>
              <SelectItem value="newest">
                Newest
              </SelectItem>

              <SelectItem value="oldest">
                Oldest
              </SelectItem>

              <SelectItem value="company">
                Company
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Status */}

        <div>
          <label
            htmlFor="status-filter"
            className="mb-2 block text-sm font-medium"
          >
            Status
          </label>

          <Select
            value={
              filters.status || "ALL"
            }
            onValueChange={
              handleStatusChange
            }
          >
            <SelectTrigger
              id="status-filter"
              className="w-full md:w-[200px]"
            >
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>

            <SelectContent>
              <SelectItem value="ALL">
                All Statuses
              </SelectItem>

              <SelectItem value="APPLIED">
                Applied
              </SelectItem>

              <SelectItem value="UNDER_REVIEW">
                Under Review
              </SelectItem>

              <SelectItem value="PHONE_SCREEN">
                Phone Screen
              </SelectItem>

              <SelectItem value="INTERVIEW">
                Interview
              </SelectItem>

              <SelectItem value="OFFER">
                Offer
              </SelectItem>

              <SelectItem value="REJECTED">
                Rejected
              </SelectItem>

              <SelectItem value="WITHDRAWN">
                Withdrawn
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* CSV Export */}

        <div>
          <label className="mb-2 block text-sm font-medium">
            Export
          </label>

          <button
            type="button"
            onClick={() =>
              exportApplicationsToCSV(
                applications
              )
            }
            disabled={
              applications.length === 0
            }
            className="rounded-md border px-4 py-2 font-medium disabled:cursor-not-allowed disabled:opacity-50"
          >
            Export CSV
          </button>
        </div>

      </div>

      {/* TanStack Table */}

      {applications.length === 0 ? (
        <p>
          No applications found.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border">

          <table className="w-full">

            <thead className="bg-muted">

              {table
                .getHeaderGroups()
                .map(
                  (headerGroup) => (
                    <tr
                      key={
                        headerGroup.id
                      }
                    >

                      {/* Selection Header */}

                      <th className="px-4 py-3 text-left text-sm font-semibold">
                        Select
                      </th>

                      {/* Table Headers */}

                      {headerGroup.headers.map(
                        (header) => (
                          <th
                            key={
                              header.id
                            }
                            className="px-4 py-3 text-left text-sm font-semibold"
                          >

                            {header.isPlaceholder ? (
                              null
                            ) : header.column.getCanSort() ? (
                              <button
                                type="button"
                                className="font-semibold"
                                onClick={header.column.getToggleSortingHandler()}
                              >
                                <table.FlexRender
                                  header={header}
                                />

                                {{
                                  asc: " ↑",
                                  desc: " ↓",
                                }[
                                  header.column.getIsSorted()
                                ] || ""}
                              </button>
                            ) : (
                              <table.FlexRender
                                header={header}
                              />
                            )}

                          </th>
                        )
                      )}

                    </tr>
                  )
                )}

            </thead>

            <tbody>

              {table
                .getRowModel()
                .rows.map(
                  (row) => (
                    <tr
                      key={row.id}
                      className="border-t"
                    >

                      {/* Row Selection */}

                      <td className="px-4 py-3">

                        <input
                          type="checkbox"
                          checked={
                            row.getIsSelected()
                          }
                          onChange={
                            row.getToggleSelectedHandler()
                          }
                        />

                      </td>

                      {/* Row Data */}

                      {row
                        .getAllCells()
                        .map(
                          (cell) => (
                            <td
                              key={
                                cell.id
                              }
                              className="px-4 py-3 text-sm align-top"
                            >
                              <table.FlexRender
                                cell={cell}
                              />
                            </td>
                          )
                        )}

                    </tr>
                  )
                )}

            </tbody>

          </table>

        </div>
      )}

      {/* Pagination */}

      <div className="flex flex-col gap-4 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between">

        {/* Previous */}

        <button
          type="button"
          disabled={
            !pagination.has_prev
          }
          onClick={() =>
            handlePageChange(
              pagination.page - 1
            )
          }
          className="rounded-md border px-4 py-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Previous
        </button>

        {/* Page Number */}

        <div className="flex items-center justify-center gap-2 text-sm">

          <span>
            Page
          </span>

          <input
            type="number"
            min="1"
            max={
              pagination.pages || 1
            }
            value={
              pagination.page
            }
            onChange={(event) =>
              handlePageChange(
                event.target.value
              )
            }
            className="w-16 rounded-md border px-2 py-1 text-center"
          />

          <span>
            of{" "}
            {pagination.pages || 1}
          </span>

        </div>

        {/* Next */}

        <button
          type="button"
          disabled={
            !pagination.has_next
          }
          onClick={() =>
            handlePageChange(
              pagination.page + 1
            )
          }
          className="rounded-md border px-4 py-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Next
        </button>

      </div>

      {/* Candidate Application Details & Timeline Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedApp?.role} at {selectedApp?.company}
            </DialogTitle>
          </DialogHeader>

          {loadingDetail ? (
            <div className="p-6 text-center text-sm text-muted-foreground">
              Loading application details & timeline...
            </div>
          ) : selectedApp ? (
            <div className="space-y-6 text-sm">
              {/* Header Info */}
              <div className="grid grid-cols-2 gap-4 bg-muted/40 p-4 rounded-lg">
                <div>
                  <span className="text-xs font-semibold uppercase text-muted-foreground">Applied Date</span>
                  <div className="font-medium text-base">
                    {selectedApp.applied_date
                      ? new Date(selectedApp.applied_date).toLocaleDateString()
                      : "N/A"}
                  </div>
                </div>
                <div>
                  <span className="text-xs font-semibold uppercase text-muted-foreground">Current Status</span>
                  <div>
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold mt-1 ${(STATUS_BADGES[selectedApp.status] || {}).color || "bg-gray-100 text-gray-800"}`}
                    >
                      {(STATUS_BADGES[selectedApp.status] || {}).label || selectedApp.status}
                    </span>
                  </div>
                </div>
                {selectedApp.notes && (
                  <div className="col-span-2">
                    <span className="text-xs font-semibold uppercase text-muted-foreground">Notes</span>
                    <p className="mt-0.5 text-muted-foreground">{selectedApp.notes}</p>
                  </div>
                )}
              </div>

              {/* Interview Information Card */}
              {selectedApp.interview_details && (
                <div className="border border-amber-300 bg-amber-50/70 dark:bg-amber-950/30 p-4 rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-amber-900 dark:text-amber-200">
                      Scheduled Interview
                    </h4>
                    <span className="text-xs bg-amber-200/70 dark:bg-amber-900 px-2 py-0.5 rounded font-medium">
                      {selectedApp.interview_details.interview_type || "Online"}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs pt-1">
                    <div>
                      <span className="font-medium text-muted-foreground">Round:</span>{" "}
                      <span className="font-semibold">{selectedApp.interview_details.interview_round}</span>
                    </div>
                    <div>
                      <span className="font-medium text-muted-foreground">Interviewer:</span>{" "}
                      <span>{selectedApp.interview_details.interviewer || "TBD"}</span>
                    </div>
                    <div>
                      <span className="font-medium text-muted-foreground">Date:</span>{" "}
                      <span>{selectedApp.interview_details.interview_date}</span>
                    </div>
                    <div>
                      <span className="font-medium text-muted-foreground">Time:</span>{" "}
                      <span>{selectedApp.interview_details.interview_time}</span>
                    </div>
                    {selectedApp.interview_details.meeting_link && (
                      <div className="col-span-2 mt-1">
                        <span className="font-medium text-muted-foreground">Join Meeting:</span>{" "}
                        <a
                          href={selectedApp.interview_details.meeting_link}
                          target="_blank"
                          rel="noreferrer"
                          className="font-medium text-blue-600 dark:text-blue-400 underline hover:text-blue-800"
                        >
                          {selectedApp.interview_details.meeting_link}
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Visual Journey Steps */}
              <div>
                <h4 className="font-semibold text-sm mb-3">Application Journey</h4>
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  {["APPLIED", "UNDER_REVIEW", "INTERVIEW", selectedApp.status === "REJECTED" ? "REJECTED" : selectedApp.status === "WITHDRAWN" ? "WITHDRAWN" : "OFFER"].map(
                    (step, idx) => {
                      const isCurrent = selectedApp.status === step;
                      const isPassed =
                        (step === "APPLIED") ||
                        (step === "UNDER_REVIEW" && ["UNDER_REVIEW", "PHONE_SCREEN", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"].includes(selectedApp.status)) ||
                        (step === "INTERVIEW" && ["INTERVIEW", "OFFER"].includes(selectedApp.status)) ||
                        (isCurrent);

                      return (
                        <div
                          key={step}
                          className={`p-2.5 rounded-lg border flex flex-col items-center ${
                            isCurrent
                              ? "border-primary bg-primary/10 font-bold"
                              : isPassed
                              ? "border-emerald-300 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-800 dark:text-emerald-300"
                              : "border-muted bg-muted/20 text-muted-foreground"
                          }`}
                        >
                          <span className="text-base mb-1">
                            {isCurrent ? "●" : isPassed ? "✓" : "○"}
                          </span>
                          <span>{(STATUS_BADGES[step] || {}).label || step}</span>
                        </div>
                      );
                    }
                  )}
                </div>
              </div>

              {/* Status History Timeline */}
              <div>
                <h4 className="font-semibold text-sm mb-3">Status Timeline</h4>
                {selectedApp.status_history && selectedApp.status_history.length > 0 ? (
                  <div className="relative border-l border-muted pl-6 space-y-4">
                    {selectedApp.status_history.map((hist, idx) => (
                      <div key={hist.id || idx} className="relative">
                        <div className="absolute -left-[31px] top-1 w-3 h-3 rounded-full bg-primary" />
                        <div className="font-medium text-sm">
                          {hist.old_status
                            ? `${(STATUS_BADGES[hist.old_status] || {}).label || hist.old_status} ➔ ${(STATUS_BADGES[hist.new_status] || {}).label || hist.new_status}`
                            : `Application Submitted (${(STATUS_BADGES[hist.new_status] || {}).label || hist.new_status})`}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {new Date(hist.changed_at).toLocaleString()}
                        </div>
                        {hist.notes && (
                          <div className="text-xs bg-muted/40 p-2 rounded mt-1 italic text-muted-foreground">
                            {hist.notes}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No timeline history recorded yet.</p>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex justify-between items-center pt-2 border-t">
                {selectedApp.status !== "WITHDRAWN" && selectedApp.status !== "REJECTED" && (
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    onClick={() => handleWithdraw(selectedApp.id)}
                  >
                    Withdraw Application
                  </Button>
                )}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="ml-auto"
                  onClick={() => setDetailModalOpen(false)}
                >
                  Close
                </Button>
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

    </div>
  );
}

export default Applications;

