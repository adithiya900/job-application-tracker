import { Link, Outlet } from 'react-router-dom';

function Layout() {
  return (
    <div>
      <nav>
        <Link to="/">Home</Link>{' '}
        <Link to="/login">Login</Link>{' '}
        <Link to="/dashboard">Dashboard</Link>{' '}
        <Link to="/applications">Applications</Link>
      </nav>

      <main>
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;