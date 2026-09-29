import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

import useApplicationStore, {
  selectFilteredApplications,
} from "../stores/applicationStore";

import ApplicationCard from "../components/ApplicationCard";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

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

  // URL -> Zustand when page loads
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

  // Fetch applications when filters or page change
  useEffect(() => {
    fetchApplications();
  }, [
    fetchApplications,
    filters.status,
    filters.search,
    filters.sort,
    pagination.page,
  ]);

  const handleStatusChange = (event) => {
    const status = event.target.value;

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

  const handleSortChange = (event) => {
    const sort = event.target.value;

    setSort(sort);

    const nextParams =
      new URLSearchParams(searchParams);

    if (sort && sort !== "newest") {
      nextParams.set("sort", sort);
    } else {
      nextParams.delete("sort");
    }

    nextParams.delete("page");

    setSearchParams(nextParams);
  };

  const handlePageChange = (page) => {
    setPage(page);

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

    if (filters.sort && filters.sort !== "newest") {
      nextParams.set(
        "sort",
        filters.sort
      );
    } else {
      nextParams.delete("sort");
    }

    if (page > 1) {
      nextParams.set(
        "page",
        String(page)
      );
    } else {
      nextParams.delete("page");
    }

    setSearchParams(nextParams);
  };

  if (loading) {
    return <p>Loading applications...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

return (
  <div>
    <h1>Applications Page</h1>

    {/* Search */}
    <div>
      <label htmlFor="search-filter">
        Search:
      </label>

      <input
        id="search-filter"
        type="text"
        value={filters.search}
        placeholder="Search company or role"
        onChange={handleSearchChange}
      />
    </div>

    {/* Sort */}
    <div className="space-y-2">
  <label
    htmlFor="sort-filter"
    className="text-sm font-medium"
  >
    Sort:
  </label>

  <Select
    value={filters.sort}
    onValueChange={(value) => {
      handleSortChange({
        target: {
          value,
        },
      });
    }}
  >
    <SelectTrigger
      id="sort-filter"
      className="w-full sm:w-[200px]"
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

    {/* Status Filter */}
    <div className="space-y-2">
  <label
    htmlFor="status-filter"
    className="text-sm font-medium"
  >
    Filter by Status:
  </label>

  <Select
    value={filters.status || "ALL"}
    onValueChange={(value) => {
      handleStatusChange({
        target: {
          value: value === "ALL" ? "" : value,
        },
      });
    }}
  >
    <SelectTrigger
      id="status-filter"
      className="w-full sm:w-[200px]"
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

    {/* Applications */}
    {applications.length === 0 ? (
      <p>No applications found.</p>
    ) : (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {applications.map((application) => (
          <ApplicationCard
            key={application.id}
            application={application}
          />
        ))}
      </div>
    )}

    {/* Pagination */}
    {pagination.pages > 1 && (
      <div>
        <button
          type="button"
          disabled={!pagination.has_prev}
          onClick={() =>
            handlePageChange(pagination.page - 1)
          }
        >
          Previous
        </button>

        <span>
          {" "}
          Page {pagination.page} of {pagination.pages}{" "}
        </span>

        <button
          type="button"
          disabled={!pagination.has_next}
          onClick={() =>
            handlePageChange(pagination.page + 1)
          }
        >
          Next
        </button>
      </div>
    )}
  </div>
)};
export default Applications;