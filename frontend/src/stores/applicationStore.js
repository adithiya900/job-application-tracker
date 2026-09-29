import { create } from "zustand";
import { devtools } from "zustand/middleware";
import api from "../services/api";

const useApplicationStore = create(
  devtools(
    (set) => ({
      applications: [],
      loading: false,
      error: "",

      filters: {
        status: "",
        search: "",
        sort: "newest",
      },

      pagination: {
        page: 1,
        per_page: 5,
        total: 0,
        pages: 0,
        has_next: false,
        has_prev: false,
      },

      fetchApplications: async () => {
        try {
          set({ loading: true, error: "" });

          const { filters, pagination } =
            useApplicationStore.getState();

          const response = await api.get("/applications", {
            params: {
              status: filters.status || undefined,
              search: filters.search || undefined,
              sort: filters.sort,
              page: pagination.page,
              per_page: pagination.per_page,
            },
          });

          set({
            applications: response.data.applications,
            pagination: response.data.pagination,
            loading: false,
          });
        } catch (error) {
          console.error(
            "Failed to fetch applications:",
            error
          );

          set({
            loading: false,
            error: "Failed to load applications.",
          });
        }
      },

      setStatusFilter: (status) => {
        set((state) => ({
          filters: {
            ...state.filters,
            status,
          },
          pagination: {
            ...state.pagination,
            page: 1,
          },
        }));
      },

      setSearchFilter: (search) => {
        set((state) => ({
          filters: {
            ...state.filters,
            search,
          },
          pagination: {
            ...state.pagination,
            page: 1,
          },
        }));
      },

      setSort: (sort) => {
        set((state) => ({
          filters: {
            ...state.filters,
            sort,
          },
          pagination: {
            ...state.pagination,
            page: 1,
          },
        }));
      },

      setPage: (page) => {
        set((state) => ({
          pagination: {
            ...state.pagination,
            page,
          },
        }));
      },

      setPerPage: (per_page) => {
        set((state) => ({
          pagination: {
            ...state.pagination,
            per_page,
            page: 1,
          },
        }));
      },

      addApplication: async (applicationData) => {
        const temporaryId = `temp-${Date.now()}`;

        const optimisticApplication = {
          id: temporaryId,
          company: applicationData.company,
          role: applicationData.role,
          status: applicationData.status,
          applied_date: applicationData.applied_date,
          notes: applicationData.notes,
          optimistic: true,
        };

        set((state) => ({
          applications: [
            optimisticApplication,
            ...state.applications,
          ],
        }));

        try {
          const response = await api.post(
            "/applications",
            applicationData
          );

          const createdApplication =
            response.data.application;

          set((state) => ({
            applications: state.applications.map(
              (application) =>
                application.id === temporaryId
                  ? createdApplication
                  : application
            ),
          }));

          return createdApplication;
        } catch (error) {
          set((state) => ({
            applications: state.applications.filter(
              (application) =>
                application.id !== temporaryId
            ),
          }));

          throw error;
        }
      },

      updateStatus: async (applicationId, status) => {
        const response = await api.put(
          `/applications/${applicationId}`,
          { status }
        );

        const updatedApplication =
          response.data.application;

        set((state) => ({
          applications: state.applications.map(
            (application) =>
              application.id === applicationId
                ? updatedApplication
                : application
          ),
        }));

        return updatedApplication;
      },
    }),
    {
      name: "application-store",
    }
  )
);

export const selectFilteredApplications = (state) => {
  const { applications, filters } = state;

  if (!filters.status) {
    return applications;
  }

  return applications.filter(
    (application) =>
      application.status === filters.status
  );
};

export default useApplicationStore;