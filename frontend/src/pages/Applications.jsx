import { useEffect } from "react";
import { useApplications } from "../contexts/ApplicationContext";

function Applications() {
  const {
    applications,
    loading,
    error,
    fetchApplications,
  } = useApplications();

  useEffect(() => {
    fetchApplications();
  }, []);

  if (loading) {
    return <p>Loading applications...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <div>
      <h1>Applications Page</h1>

      {applications.length === 0 ? (
        <p>No applications found.</p>
      ) : (
        applications.map((application) => (
          <div key={application.id}>
            <h3>{application.company}</h3>
            <p>{application.role}</p>
            <p>{application.status}</p>
            <p>{application.applied_date}</p>
            <p>{application.notes}</p>

            {application.optimistic && (
              <p>Saving...</p>
            )}
          </div>
        ))
      )}
    </div>
  );
}

export default Applications;
