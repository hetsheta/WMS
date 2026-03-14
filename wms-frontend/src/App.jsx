import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import { getMe } from './lib/api'
import Layout from './components/layout/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import ForgotPassword from './pages/ForgotPassword'
import Dashboard from './pages/Dashboard'
import Stock from './pages/Stock'
import Operations from './pages/Operations'
import OperationDetail from './pages/OperationDetail'
import Products from './pages/Products'
import Warehouses from './pages/Warehouses'
import History from './pages/History'

function PrivateRoute({ children }) {
  const token = useAuthStore((s) => s.token)
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  const { token, setAuth, logout } = useAuthStore()

  useEffect(() => {
    if (!token) return
    getMe()
      .then((r) => setAuth(r.data, token, localStorage.getItem('refresh_token')))
      .catch(() => logout())
  }, [token, setAuth, logout])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="stock" element={<Stock />} />
          <Route path="operations" element={<Operations />} />
          <Route path="operations/:id" element={<OperationDetail />} />
          <Route path="products" element={<Products />} />
          <Route path="warehouses" element={<Warehouses />} />
          <Route path="history" element={<History />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
