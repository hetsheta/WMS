import React, { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/auth'
import { queryClient } from '../../main'
import {
  LayoutDashboard, Package, ArrowLeftRight, Boxes,
  Warehouse, LogOut, Menu, X, ChevronRight, History as HistoryIcon
} from 'lucide-react'
import clsx from 'clsx'

const nav = [
  { to: '/dashboard',  icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/stock',      icon: Boxes,           label: 'Stock' },
  { to: '/operations', icon: ArrowLeftRight,  label: 'Operations' },
  { to: '/history',    icon: HistoryIcon,     label: 'Move History' },
  { to: '/products',   icon: Package,         label: 'Products' },
  { to: '/warehouses', icon: Warehouse,       label: 'Warehouses' },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const handleLogout = () => {
    queryClient.clear()
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      {/* Mobile overlay */}
      {open && (
        <div className="fixed inset-0 z-20 bg-black/60 lg:hidden" onClick={() => setOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={clsx(
        'fixed inset-y-0 left-0 z-30 flex flex-col w-56 bg-surface-1 border-r border-border transition-transform duration-200',
        'lg:static lg:translate-x-0',
        open ? 'translate-x-0' : '-translate-x-full'
      )}>
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-border">
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center">
            <Warehouse size={14} className="text-white" />
          </div>
          <span className="font-semibold text-white tracking-tight">WMS</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) => clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group',
                isActive
                  ? 'bg-accent/15 text-accent-light'
                  : 'text-muted hover:text-slate-200 hover:bg-surface-2'
              )}
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="px-3 py-4 border-t border-border">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center text-accent-light text-xs font-semibold">
              {user?.full_name?.[0]?.toUpperCase() ?? 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-slate-300 truncate">{user?.full_name}</p>
              <p className="text-xs text-muted truncate">{user?.email}</p>
            </div>
          </div>
          <button onClick={handleLogout} className="mt-1 w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted hover:text-danger hover:bg-danger/10 transition-all">
            <LogOut size={15} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar (mobile) */}
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-border bg-surface-1">
          <button onClick={() => setOpen(true)} className="text-muted hover:text-white">
            <Menu size={20} />
          </button>
          <span className="font-semibold text-white">WMS</span>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
