import React from 'react'
import { useQuery } from 'react-query'
import { getDashboard, getOperations, getStock } from '../lib/api'
import { useAuthStore } from '../store/auth'
import { ArrowDownCircle, ArrowUpCircle, Clock, Package, AlertTriangle, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import clsx from 'clsx'

const LOW_STOCK_THRESHOLD = 10

function StatusBadge({ status }) {
  return <span className={`badge-${status}`}>{status}</span>
}

export default function Dashboard() {
  const user = useAuthStore((s) => s.user)
  const { data: stats } = useQuery('dashboard', () => getDashboard().then((r) => r.data))
  const { data: recentOps } = useQuery('recent-ops', () =>
    getOperations({ limit: 8 }).then((r) => r.data.items)
  )
  const { data: stock = [] } = useQuery('dashboard-stock', () =>
    getStock({ limit: 200 }).then((r) => r.data)
  )

  const lowStockItems = stock
    .filter((item) => parseFloat(item.free_to_use) <= LOW_STOCK_THRESHOLD)
    .sort((left, right) => parseFloat(left.free_to_use) - parseFloat(right.free_to_use))
    .slice(0, 8)

  const topCards = stats ? [
    { label: 'Total Products', value: stats.total_products, icon: Package, color: 'text-blue-400' },
    { label: 'Low Stock Alerts', value: stats.low_stock_items, icon: AlertTriangle, color: 'text-red-400' },
  ] : []

  const statCards = stats ? [
    { label: 'Receipts today', value: stats.receipts_today, icon: ArrowDownCircle, color: 'text-indigo-400' },
    { label: 'Receipts pending', value: stats.receipts_pending, icon: Clock, color: 'text-amber-400' },
    { label: 'Deliveries today', value: stats.deliveries_today, icon: ArrowUpCircle, color: 'text-purple-400' },
    { label: 'Deliveries pending', value: stats.deliveries_pending, icon: Clock, color: 'text-amber-400' },
    { label: 'Internal today', value: stats.internal_today, icon: RefreshCw, color: 'text-emerald-400' },
    { label: 'Internal pending', value: stats.internal_pending, icon: Clock, color: 'text-amber-400' },
  ] : []

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-semibold text-white">
          Good {new Date().getHours() < 12 ? 'morning' : 'afternoon'},{' '}
          {user?.full_name?.split(' ')[0]}
        </h1>
        <p className="text-sm text-muted mt-1">{format(new Date(), 'EEEE, MMMM d, yyyy')}</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-2 xl:grid-cols-4 gap-3">
        {topCards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="stat-card border-border/80 bg-surface/50">
            <div className="flex items-center justify-between">
              <div className="stat-label">{label}</div>
              <Icon size={18} className={clsx(color)} />
            </div>
            <div className="stat-value mt-2 text-2xl">{value ?? '—'}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="stat-card">
            <Icon size={16} className={clsx(color, 'mb-1')} />
            <div className="stat-value">{value ?? '—'}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link to="/operations?op_type=receipt" className="card block hover:border-accent/50 transition-colors">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Receipt Operations</h2>
              <p className="text-sm text-muted mt-1">Create and track inbound receipts.</p>
            </div>
            <ArrowDownCircle size={20} className="text-indigo-400" />
          </div>
          <div className="mt-4 flex gap-6 text-sm">
            <div>
              <div className="text-xs text-muted uppercase tracking-wider">Today</div>
              <div className="font-mono text-xl text-white">{stats?.receipts_today ?? 0}</div>
            </div>
            <div>
              <div className="text-xs text-muted uppercase tracking-wider">Pending</div>
              <div className="font-mono text-xl text-amber-300">{stats?.receipts_pending ?? 0}</div>
            </div>
            <div>
              <div className="text-xs text-muted uppercase tracking-wider">Waiting</div>
              <div className="font-mono text-xl text-indigo-300">{stats?.receipts_waiting ?? 0}</div>
            </div>
          </div>
        </Link>

        <Link to="/operations?op_type=delivery" className="card block hover:border-accent/50 transition-colors">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Delivery Operations</h2>
              <p className="text-sm text-muted mt-1">Manage outbound deliveries and dispatch.</p>
            </div>
            <ArrowUpCircle size={20} className="text-purple-400" />
          </div>
          <div className="mt-4 flex gap-6 text-sm">
            <div>
              <div className="text-xs text-muted uppercase tracking-wider">Today</div>
              <div className="font-mono text-xl text-white">{stats?.deliveries_today ?? 0}</div>
            </div>
            <div>
              <div className="text-xs text-muted uppercase tracking-wider">Pending</div>
              <div className="font-mono text-xl text-amber-300">{stats?.deliveries_pending ?? 0}</div>
            </div>
            <div>
              <div className="text-xs text-muted uppercase tracking-wider">Waiting</div>
              <div className="font-mono text-xl text-purple-300">{stats?.deliveries_waiting ?? 0}</div>
            </div>
          </div>
        </Link>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-medium text-white text-sm">Low Stock Details</h2>
            <p className="text-xs text-muted mt-1">Items with free-to-use stock at or below {LOW_STOCK_THRESHOLD}</p>
          </div>
          <Link to="/stock" className="text-xs text-accent hover:text-accent-light">Open stock →</Link>
        </div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Location</th>
                <th>On hand</th>
                <th>Reserved</th>
                <th>Free to use</th>
              </tr>
            </thead>
            <tbody>
              {lowStockItems.length === 0 && (
                <tr><td colSpan={5} className="text-center text-muted py-8">No low stock items</td></tr>
              )}
              {lowStockItems.map((item) => (
                <tr key={item.id}>
                  <td className="text-white font-medium">{item.product?.name || item.product_id}</td>
                  <td className="text-muted text-xs">{item.location?.name || item.location_id}</td>
                  <td className="font-mono">{item.on_hand}</td>
                  <td className="font-mono text-amber-400">{item.reserved}</td>
                  <td className="font-mono text-danger font-semibold">{item.free_to_use}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-medium text-white text-sm">Recent Operations</h2>
          <Link to="/operations" className="text-xs text-accent hover:text-accent-light">View all →</Link>
        </div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Type</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {recentOps?.length === 0 && (
                <tr><td colSpan={4} className="text-center text-muted py-8">No operations yet</td></tr>
              )}
              {recentOps?.map((op) => (
                <tr key={op.id}>
                  <td>
                    <Link to={`/operations/${op.id}`} className="font-mono text-accent-light hover:underline text-xs">
                      {op.reference}
                    </Link>
                  </td>
                  <td><span className={`badge-${op.operation_type}`}>{op.operation_type}</span></td>
                  <td><StatusBadge status={op.status} /></td>
                  <td className="text-muted text-xs">{format(new Date(op.created_at), 'MMM d, HH:mm')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
