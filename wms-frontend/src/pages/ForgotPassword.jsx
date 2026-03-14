import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { KeyRound, ArrowLeft } from 'lucide-react'
import { forgotPassword, resetPassword } from '../lib/api'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [token, setToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [requestComplete, setRequestComplete] = useState(false)

  const handleRequest = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await forgotPassword(email)
      if (data.reset_token) {
        setToken(data.reset_token)
      }
      setRequestComplete(true)
      toast.success(data.message || 'Reset instructions generated')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Unable to process request')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await resetPassword(token, newPassword)
      toast.success(data.message || 'Password reset successful')
      setToken('')
      setNewPassword('')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Unable to reset password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.03)_1px,transparent_1px)] bg-[size:48px_48px]" />
      <div className="relative w-full max-w-md">
        <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-64 h-64 bg-accent/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative card border-border/80">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-accent/15 border border-accent/30 mb-4">
              <KeyRound size={22} className="text-accent-light" />
            </div>
            <h1 className="text-xl font-semibold text-white">Reset Password</h1>
            <p className="text-sm text-muted mt-1">Request a reset token, then set a new password.</p>
          </div>

          <form onSubmit={handleRequest} className="space-y-4">
            <div>
              <label className="label">Email Address</label>
              <input
                type="email"
                className="input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@wms.com"
                required
              />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-2.5 mt-2">
              {loading ? 'Requesting...' : 'Request Reset'}
            </button>
          </form>

          {requestComplete && (
            <div className="mt-6 space-y-4">
              <div className="bg-emerald-500/10 text-emerald-400 p-4 rounded-xl border border-emerald-500/20 text-sm">
                Reset request processed. If the account exists, a reset token was generated.
              </div>

              <form onSubmit={handleReset} className="space-y-4">
                <div>
                  <label className="label">Reset Token</label>
                  <textarea
                    className="input min-h-[96px] resize-none font-mono text-xs"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="Paste the reset token here"
                    required
                  />
                </div>
                <div>
                  <label className="label">New Password</label>
                  <input
                    type="password"
                    className="input"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    minLength={8}
                    required
                  />
                </div>
                <button type="submit" disabled={loading || !token} className="btn-primary w-full justify-center py-2.5">
                  {loading ? 'Resetting...' : 'Set New Password'}
                </button>
              </form>
            </div>
          )}

          <div className="text-center mt-6 text-sm">
            <Link to="/login" className="inline-flex items-center text-muted hover:text-white transition-colors">
              <ArrowLeft size={14} className="mr-2" />
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
