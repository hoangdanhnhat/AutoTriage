import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Layout from './components/layout/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Inventories from './pages/Inventories'
import InventoryDetail from './pages/InventoryDetail'
import TriageList from './pages/TriageList'
import TriageNew from './pages/TriageNew'
import TriageDetail from './pages/TriageDetail'

function PrivateRoute({ children }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="inventories" element={<Inventories />} />
          <Route path="inventories/:id" element={<InventoryDetail />} />
          <Route path="triage" element={<TriageList />} />
          <Route path="triage/new" element={<TriageNew />} />
          <Route path="triage/:id" element={<TriageDetail />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
