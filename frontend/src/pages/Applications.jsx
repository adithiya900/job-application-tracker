
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

      const updateStatus = useApplicationStore(
        (state) => state.updateStatus
      );

      return (
        <Select
          value={application.status}
          onValueChange={(value) =>
            updateStatus(application.id, value)
          }
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="APPLIED">
              Applied
            </SelectItem>
            <SelectItem value="INTERVIEW">
              Interview
            </SelectItem>
            <SelectItem value="OFFER">
              Selected
            </SelectItem>
            <SelectItem value="REJECTED">
              Rejected
            </SelectItem>
          </SelectContent>
        </Select>
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
                All
              </SelectItem>

              <SelectItem value="APPLIED">
                Applied
              </SelectItem>

              <SelectItem value="INTERVIEW">
                Interview
              </SelectItem>

              <SelectItem value="OFFER">
                Selected
              </SelectItem>

              <SelectItem value="REJECTED">
                Rejected
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

    </div>
  );
}

export default Applications;

