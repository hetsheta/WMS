import axios from 'axios'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export const api = axios.create({
  baseURL: apiBaseUrl,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401 && !err.config.url.includes('/auth/login')) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────
export const login = (email, password) =>
  api.post('/auth/login', { email, password })

export const getMe = () => api.get('/auth/me')
export const forgotPassword = (email) => api.post('/auth/forgot-password', { email })
export const resetPassword = (token, new_password) =>
  api.post('/auth/reset-password', { token, new_password })

// ── Dashboard ─────────────────────────────────────────────────────────────
export const getDashboard = () => api.get('/dashboard')

// ── Warehouses ────────────────────────────────────────────────────────────
export const getWarehouses = () => api.get('/warehouses')
export const createWarehouse = (data) => api.post('/warehouses', data)
export const getLocations = (id) => api.get(`/warehouses/${id}/locations`)
export const createLocation = (id, data) => api.post(`/warehouses/${id}/locations`, data)

// ── Products ──────────────────────────────────────────────────────────────
export const getProducts = (params) => api.get('/products', { params })
export const createProduct = (data) => api.post('/products', data)
export const updateProduct = (id, data) => api.patch(`/products/${id}`, data)

// ── Stock ─────────────────────────────────────────────────────────────────
export const getStock = (params) => api.get('/stock', { params })
export const adjustStock = (data) => api.post('/stock/adjust', data)

// ── Operations ────────────────────────────────────────────────────────────
export const getOperations = (params) => api.get('/operations', { params })
export const getOperation = (id) => api.get(`/operations/${id}`)
export const createOperation = (data) => api.post('/operations', data)
export const validateOperation = (id) => api.post(`/operations/${id}/validate`)
export const markReady = (id) => api.post(`/operations/${id}/ready`)
export const confirmOperation = (id, quantities) => api.post(`/operations/${id}/confirm`, quantities)
export const cancelOperation = (id) => api.post(`/operations/${id}/cancel`)
export const getMoveHistory = (params) => api.get('/operations/history', { params })
