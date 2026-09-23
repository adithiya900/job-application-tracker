import { useEffect } from 'react';

function Dashboard() {
  useEffect(() => {
    document.title = 'Dashboard - Job Application Tracker';
  }, []);

  return (
    <div>
      <h1>Dashboard Page</h1>
      <p>View your job application statistics here</p>
    </div>
  );
}

export default Dashboard;