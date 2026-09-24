import { createContext, useContext, useState } from "react";
import api from "../services/api";

const ApplicationContext = createContext();

export function ApplicationProvider({ children }) {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchApplications = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/applications");

      setApplications(response.data.applications);
    } catch (error) {
      console.error("Failed to fetch applications:", error);
      setError("Failed to load applications.");
    } finally {
      setLoading(false);
    }
  };

  const addApplicationOptimistically = async (applicationData) => {
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

    setApplications((currentApplications) => [
      optimisticApplication,
      ...currentApplications,
    ]);

    try {
      const response = await api.post("/applications", applicationData);

      const createdApplication = response.data.application;

      setApplications((currentApplications) =>
        currentApplications.map((application) =>
          application.id === temporaryId
            ? createdApplication
            : application
        )
      );

      return createdApplication;
    } catch (error) {
      setApplications((currentApplications) =>
        currentApplications.filter(
          (application) => application.id !== temporaryId
        )
      );

      throw error;
    }
  };

  return (
    <ApplicationContext.Provider
      value={{
        applications,
        loading,
        error,
        fetchApplications,
        addApplicationOptimistically,
      }}
    >
      {children}
    </ApplicationContext.Provider>
  );
}

export function useApplications() {
  return useContext(ApplicationContext);
}
