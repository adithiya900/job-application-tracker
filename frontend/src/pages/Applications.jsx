import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

import {
  createPaginatedRowModel,
  createSortedRowModel,
  rowPaginationFeature,
  rowSelectionFeature,
  rowSortingFeature,
  tableFeatures,
  useTable,
} from "@tanstack/react-table";

import useApplicationStore, {
  selectFilteredApplications,
} from "../stores/applicationStore";

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
  },
  {
    accessorKey: "applied_date",
    header: "Applied Date",
  },
  {
    accessorKey: "notes",
    header: "Notes",
  },
];

// --------------------------------------------------
// CSV Export
// --------------------------------------------------

const exportApplicationsToCSV = (applications) => {
  const headers = [
    "Company",
    "Role",
    "Status",
    "Applied Date",
    "Notes",
  ];

  const rows = applications.map((application) => [
    application.company,
    application.role,
    application.status,
    application.applied_date,
    application.notes,
  ]);

  const csvContent = [
    headers,
    ...rows,
  ]
    .map((row) =>
      row
        .map((value) => {
          const text = value ?? "";

          return `"${String(text).replace(/"/g, '""')}"`;
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

function Applications() {
  const [searchParams, setSearchParams] =
    useSearchParams();

  const applications = useApplicationStore(
    selectFilteredApplications
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
  // Fetch applications whenever filters/page change
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
  // Status filter
  // --------------------------------------------------

  const handleStatusChange = (value) => {
    const status =
      value === "ALL" ? "" : value;

    setStatusFilter(status);

    const nextParams =
      new URLSearchParams(searchParams);

    if (status) {
      nextParams.set("status", status);
    } else {
      nextParams.delete("status");
    }

    nextParams.delete("page");

    setSearchParams(nextParams);
  };

  // --------------------------------------------------
  // Search filter
  // --------------------------------------------------

  const handleSearchChange = (event) => {
    const search = event.target.value;

    setSearchFilter(search);

    const nextParams =
      new URLSearchParams(searchParams);

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

    if (value && value !== "newest") {
      nextParams.set("sort", value);
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
      Math.max(requestedPage, 1),
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
  // Loading
  // --------------------------------------------------

  if (loading) {
    return (
      <p>
        Loading applications...
      </p>
    );
  }

  // --------------------------------------------------
  // Error
  // --------------------------------------------------

  if (error) {
    return (
      <p>
        {error}
      </p>
    );
  }

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
            value={filters.status || "ALL"}
            onValueChange={handleStatusChange}
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
              exportApplicationsToCSV(applications)
            }
            disabled={applications.length === 0}
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

              {table.getHeaderGroups().map(
                (headerGroup) => (
                  <tr key={headerGroup.id}>

                    {/* Selection Header */}

                    <th className="px-4 py-3 text-left text-sm font-semibold">
                      Select
                    </th>

                    {/* Table Headers */}

                    {headerGroup.headers.map(
                      (header) => (
                        <th
                          key={header.id}
                          className="px-4 py-3 text-left text-sm font-semibold"
                        >
                          {header.isPlaceholder ? (
                            null
                          ) : (
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
                .rows.map((row) => (
                  <tr
                    key={row.id}
                    className="border-t"
                  >

                    {/* Row Selection */}

                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={row.getIsSelected()}
                        onChange={
                          row.getToggleSelectedHandler()
                        }
                      />
                    </td>

                    {/* Row Data */}

                    {row.getAllCells().map(
                      (cell) => (
                        <td
                          key={cell.id}
                          className="px-4 py-3 text-sm"
                        >
                          <table.FlexRender
                            cell={cell}
                          />
                        </td>
                      )
                    )}

                  </tr>
                ))}

            </tbody>

          </table>

        </div>
      )}

      {/* Pagination */}

      <div className="flex flex-col gap-4 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between">

        {/* Previous */}

        <button
          type="button"
          disabled={!pagination.has_prev}
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
            max={pagination.pages || 1}
            value={pagination.page}
            onChange={(event) =>
              handlePageChange(
                event.target.value
              )
            }
            className="w-16 rounded-md border px-2 py-1 text-center"
          />

          <span>
            of {pagination.pages || 1}
          </span>

        </div>

        {/* Next */}

        <button
          type="button"
          disabled={!pagination.has_next}
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