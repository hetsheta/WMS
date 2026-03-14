import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { login, getMe } from '../lib/api'
import { queryClient } from '../main'
import toast from 'react-hot-toast'
import { Warehouse, Eye, EyeOff } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [form, setForm] = useState({ email: 'admin@wms.com', password: 'admin1234' })
  const [loading, setLoading] = useState(false)
  const [showPw, setShowPw] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await login(form.email, form.password)
      queryClient.clear()
      setAuth(
        {
          email: form.email,
          full_name: 'Loading profile',
          is_active: true,
          is_superuser: false,
        },
        data.access_token,
        data.refresh_token
      )
      window.location.href = '/dashboard'
      getMe()
        .then((me) => {
          setAuth(me.data, data.access_token, data.refresh_token)
        })
        .catch(() => {})
    } catch {
      toast.error('Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      {/* Background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.03)_1px,transparent_1px)] bg-[size:48px_48px]" />

      <div className="relative w-full max-w-sm">
        {/* Glow */}
        <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-64 h-64 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative card border-border/80">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-accent/15 border border-accent/30 mb-4">
              <Warehouse size={22} className="text-accent-light" />
            </div>
            <h1 className="text-xl font-semibold text-white">Warehouse Management</h1>
            <p className="text-sm text-muted mt-1">Sign in to continue</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                className="input"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="admin@wms.com"
                required
              />
            </div>
            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  className="input pr-10"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-slate-300"
                >
                  {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-2.5 mt-2">
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          <div className="text-center mt-6 text-sm text-muted">Don't have an account? <a href="/register" className="text-accent hover:text-accent-light font-medium">Sign up</a></div><div className="text-center mt-2 text-sm"><a href="/forgot-password" id="forgot-password-link" className="text-muted hover:text-white transition-colors">Forgot password?</a></div></form>
        </div>
      </div>
    </div>
  )
}
