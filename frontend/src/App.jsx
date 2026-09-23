import { BrowserRouter, Routes, Route } from 'react-router-dom';

import Layout from './components/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Applications from './pages/Applications';
import ComponentsDemo from './pages/ComponentsDemo';
import AddApplication from './pages/AddApplication';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="login" element={<Login />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="applications" element={<Applications />} />
          <Route path="components-demo" element={<ComponentsDemo />} />
          <Route path="applications/add" element={<AddApplication />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;