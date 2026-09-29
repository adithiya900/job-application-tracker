import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

import useApplicationStore, {
  selectFilteredApplications,
} from "../stores/applicationStore";

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
      <div>
        <label htmlFor="sort-filter">
          Sort:
        </label>

        <select
          id="sort-filter"
          value={filters.sort}
          onChange={handleSortChange}
        >
          <option value="newest">
            Newest
          </option>

          <option value="oldest">
            Oldest
          </option>

          <option value="company">
            Company
          </option>
        </select>
      </div>

      {/* Status Filter */}
      <div>
        <label htmlFor="status-filter">
          Filter by Status:
        </label>

        <select
          id="status-filter"
          value={filters.status}
          onChange={handleStatusChange}
        >
          <option value="">
            All
          </option>

          <option value="APPLIED">
            Applied
          </option>

          <option value="INTERVIEW">
            Interview
          </option>

          <option value="OFFER">
            Selected
          </option>

          <option value="REJECTED">
            Rejected
          </option>
        </select>
      </div>

      {/* Applications */}
      {applications.length === 0 ? (
        <p>No applications found.</p>
      ) : (
        applications.map((application) => (
          <div key={application.id}>
            <h3>
              {application.company}
            </h3>

            <p>
              {application.role}
            </p>

            <p>
              {application.status}
            </p>

            <p>
              {application.applied_date}
            </p>

            <p>
              {application.notes}
            </p>

            {application.optimistic && (
              <p>Saving...</p>
            )}
          </div>
        ))
      )}

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div>
          <button
            type="button"
            disabled={!pagination.has_prev}
            onClick={() =>
              handlePageChange(
                pagination.page - 1
              )
            }
          >
            Previous
          </button>

          <span>
            {" "}
            Page {pagination.page} of{" "}
            {pagination.pages}{" "}
          </span>

          <button
            type="button"
            disabled={!pagination.has_next}
            onClick={() =>
              handlePageChange(
                pagination.page + 1
              )
            }
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default Applications;