import React, { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { getOperations, getWarehouses, createOperation, getProducts, getLocations } from '../lib/api'
import { Link, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Plus, X, Trash2, ArrowRight } from 'lucide-react'
import { format } from 'date-fns'

const STATUSES = ['', 'draft', 'validated', 'ready', 'done', 'cancelled']
const TYPES = ['', 'receipt', 'delivery', 'internal', 'adjustment']

export default function Operations() {
  const qc = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [filters, setFilters] = useState({
    q: searchParams.get('q') ?? '',
    op_type: '',
    status: '',
  })
  const [showCreate, setShowCreate] = useState(false)
  const [recentOperations, setRecentOperations] = useState([])
  const [form, setForm] = useState({
    operation_type: 'receipt',
    warehouse_id: '',
    partner_name: '',
    external_reference: '',
    responsible_name: '',
    scheduled_date: '',
    notes: '',
    lines: [],
  })
  const [newLine, setNewLine] = useState({ product_id: '', location_id: '', dest_location_id: '', qty_demand: '' })
  const [selectedWarehouse, setSelectedWarehouse] = useState('')

  const { data, isLoading } = useQuery(
    ['operations', filters],
    () => {
      const params = { ...filters, limit: 50 }
      Object.keys(params).forEach((key) => {
        if (params[key] === '') delete params[key]
      })
      return getOperations(params).then((r) => r.data)
    },
    { keepPreviousData: true }
  )
  const { data: warehouses = [] } = useQuery('warehouses', () => getWarehouses().then((r) => r.data))
  const { data: products = [] } = useQuery('products-all', () => getProducts({ limit: 200 }).then((r) => r.data.items ?? []))
  const { data: locations = [] } = useQuery(
    ['locations', selectedWarehouse],
    () => selectedWarehouse ? getLocations(selectedWarehouse).then((r) => r.data) : [],
    { enabled: !!selectedWarehouse }
  )

  const createMut = useMutation(createOperation, {
    onSuccess: (response) => {
      const createdOperation = response?.data
      toast.success('Operation created')
      const clearedFilters = { q: '', op_type: '', status: '' }
      setFilters(clearedFilters)
      setSearchParams({}, { replace: true })
      if (createdOperation) {
        setRecentOperations((current) => [createdOperation, ...current.filter((item) => item.id !== createdOperation.id)])
      }
      qc.setQueryData(['operations', clearedFilters], (current) => {
        const existingItems = current?.items ?? []
        const nextItems = createdOperation ? [createdOperation, ...existingItems] : existingItems
        return {
          total: createdOperation ? (current?.total ?? 0) + 1 : current?.total ?? 0,
          page: 1,
          size: current?.size ?? 50,
          items: nextItems,
        }
      })
      qc.invalidateQueries('operations')
      qc.invalidateQueries('dashboard')
      setShowCreate(false)
      setForm({
        operation_type: 'receipt',
        warehouse_id: '',
        partner_name: '',
        external_reference: '',
        responsible_name: '',
        scheduled_date: '',
        notes: '',
        lines: [],
      })
    },
    onError: (e) => toast.error(e.response?.data?.detail ?? 'Failed'),
  })

  const addLine = () => {
    if (!newLine.product_id || !newLine.location_id || !newLine.qty_demand) return
    if (form.operation_type === 'internal' && !newLine.dest_location_id) return
    const lineData = { ...newLine, qty_demand: parseFloat(newLine.qty_demand) }
    if (form.operation_type !== 'internal') delete lineData.dest_location_id
    setForm((current) => ({ ...current, lines: [...current.lines, lineData] }))
    setNewLine({ product_id: '', location_id: '', dest_location_id: '', qty_demand: '' })
  }

  const submit = () => {
    const payload = {
      ...form,
      scheduled_date: form.scheduled_date ? new Date(form.scheduled_date).toISOString() : null,
    }
    if (!payload.notes) delete payload.notes
    if (!payload.partner_name) delete payload.partner_name
    if (!payload.external_reference) delete payload.external_reference
    if (!payload.responsible_name) delete payload.responsible_name
    if (!payload.scheduled_date) delete payload.scheduled_date
    createMut.mutate(payload)
  }

  const ops = useMemo(() => {
    const fetched = data?.items ?? []
    const merged = [...fetched, ...recentOperations]
    return merged.filter((item, index, items) => items.findIndex((entry) => entry.id === item.id) === index)
  }, [data, recentOperations])
  const updateFilters = (next) => {
    setFilters(next)
    const params = new URLSearchParams()
    if (next.q) params.set('q', next.q)
    setSearchParams(params, { replace: true })
  }

  const resetFilters = () => {
    updateFilters({ q: '', op_type: '', status: '' })
  }

  return (
    <div className="space-y-5 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Operations</h1>
          <p className="text-sm text-muted mt-0.5">Receipts, deliveries, transfers and adjustments</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus size={15} /> New operation
        </button>
      </div>

      <div className="flex gap-3 flex-wrap">
        <input
          className="input max-w-xs"
          value={filters.q}
          onChange={(e) => updateFilters({ ...filters, q: e.target.value })}
          placeholder="Search by reference"
        />
        <select
          className="input max-w-[160px]"
          value={filters.op_type}
          onChange={(e) => updateFilters({ ...filters, op_type: e.target.value })}
        >
          {TYPES.map((type) => <option key={type} value={type}>{type || 'All types'}</option>)}
        </select>
        <select
          className="input max-w-[160px]"
          value={filters.status}
          onChange={(e) => updateFilters({ ...filters, status: e.target.value })}
        >
          {STATUSES.map((status) => <option key={status} value={status}>{status || 'All statuses'}</option>)}
        </select>
        {(filters.q || filters.op_type || filters.status) && (
          <button onClick={resetFilters} className="btn-ghost">
            Clear filters
          </button>
        )}
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Type</th>
                <th>Status</th>
                <th>Lines</th>
                <th>Scheduled</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && <tr><td colSpan={6} className="text-center text-muted py-10">Loading...</td></tr>}
              {!isLoading && ops.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center text-muted py-10">
                    {filters.q || filters.op_type || filters.status ? 'No operations match the current filters' : 'No operations found'}
                  </td>
                </tr>
              )}
              {ops.map((op) => (
                <tr key={op.id}>
                  <td>
                    <Link to={`/operations/${op.id}`} className="font-mono text-accent-light hover:underline text-xs">
                      {op.reference}
                    </Link>
                  </td>
                  <td><span className={`badge-${op.operation_type}`}>{op.operation_type}</span></td>
                  <td><span className={`badge-${op.status}`}>{op.status}</span></td>
                  <td className="font-mono text-muted">{op.move_lines?.length ?? 0}</td>
                  <td className="text-muted text-xs">
                    {op.scheduled_date ? format(new Date(op.scheduled_date), 'MMM d') : '—'}
                  </td>
                  <td className="text-muted text-xs">{format(new Date(op.created_at), 'MMM d, HH:mm')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="card w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-semibold text-white">New Operation</h2>
              <button onClick={() => setShowCreate(false)} className="text-muted hover:text-white"><X size={18} /></button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Type</label>
                  <select
                    className="input"
                    value={form.operation_type}
                    onChange={(e) => setForm((current) => ({ ...current, operation_type: e.target.value, lines: [] }))}
                  >
                    <option value="receipt">Receipt (In)</option>
                    <option value="delivery">Delivery (Out)</option>
                    <option value="internal">Internal Transfer</option>
                    <option value="adjustment">Stock Adjustment</option>
                  </select>
                </div>
                <div>
                  <label className="label">Warehouse</label>
                  <select
                    className="input"
                    value={form.warehouse_id}
                    onChange={(e) => {
                      setForm((current) => ({ ...current, warehouse_id: e.target.value, lines: [] }))
                      setSelectedWarehouse(e.target.value)
                    }}
                  >
                    <option value="">Select...</option>
                    {warehouses.map((warehouse) => <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">
                    {form.operation_type === 'receipt' ? 'Supplier' : form.operation_type === 'delivery' ? 'Customer' : 'Party'}
                  </label>
                  <input
                    className="input"
                    value={form.partner_name}
                    onChange={(e) => setForm((current) => ({ ...current, partner_name: e.target.value }))}
                    placeholder={form.operation_type === 'receipt' ? 'Supplier name' : 'Customer name'}
                  />
                </div>
                <div>
                  <label className="label">
                    {form.operation_type === 'receipt' ? 'Receipt Ref' : form.operation_type === 'delivery' ? 'Order Ref' : 'External Ref'}
                  </label>
                  <input
                    className="input"
                    value={form.external_reference}
                    onChange={(e) => setForm((current) => ({ ...current, external_reference: e.target.value }))}
                    placeholder="Optional reference"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Responsible</label>
                  <input
                    className="input"
                    value={form.responsible_name}
                    onChange={(e) => setForm((current) => ({ ...current, responsible_name: e.target.value }))}
                    placeholder="Person handling this operation"
                  />
                </div>
                <div>
                  <label className="label">Scheduled Date</label>
                  <input
                    type="datetime-local"
                    className="input"
                    value={form.scheduled_date}
                    onChange={(e) => setForm((current) => ({ ...current, scheduled_date: e.target.value }))}
                  />
                </div>
              </div>

              <div>
                <label className="label">Notes</label>
                <input
                  className="input"
                  value={form.notes}
                  onChange={(e) => setForm((current) => ({ ...current, notes: e.target.value }))}
                  placeholder="Optional notes"
                />
              </div>

              <div>
                <label className="label">Product Lines</label>
                {form.lines.map((line, index) => (
                  <div key={index} className="flex items-center gap-2 mb-2 text-xs bg-surface-2 rounded-lg px-3 py-2">
                    <span className="flex-1 text-muted font-mono truncate">{products.find((product) => product.id === line.product_id)?.name || line.product_id}</span>
                    <span className="text-muted flex items-center gap-2">
                      {locations.find((location) => location.id === line.location_id)?.name || line.location_id}
                      {form.operation_type === 'internal' && (
                        <>
                          <ArrowRight size={12} />
                          {locations.find((location) => location.id === line.dest_location_id)?.name || line.dest_location_id}
                        </>
                      )}
                    </span>
                    <span className="font-mono text-white ml-2">{line.qty_demand}</span>
                    <button
                      onClick={() => setForm((current) => ({ ...current, lines: current.lines.filter((_, lineIndex) => lineIndex !== index) }))}
                      className="text-muted hover:text-danger ml-2"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}

                <div className={`grid gap-2 mt-2 ${form.operation_type === 'internal' ? 'grid-cols-4' : 'grid-cols-3'}`}>
                  <select className="input text-xs" value={newLine.product_id} onChange={(e) => setNewLine((current) => ({ ...current, product_id: e.target.value }))}>
                    <option value="">Product...</option>
                    {products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
                  </select>
                  <select className="input text-xs" value={newLine.location_id} onChange={(e) => setNewLine((current) => ({ ...current, location_id: e.target.value }))}>
                    <option value="">{form.operation_type === 'internal' ? 'From...' : 'Location...'}</option>
                    {locations.map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}
                  </select>
                  {form.operation_type === 'internal' && (
                    <select className="input text-xs" value={newLine.dest_location_id} onChange={(e) => setNewLine((current) => ({ ...current, dest_location_id: e.target.value }))}>
                      <option value="">To...</option>
                      {locations.map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}
                    </select>
                  )}
                  <div className="flex gap-1">
                    <input
                      type="number"
                      className="input text-xs"
                      placeholder="Qty"
                      value={newLine.qty_demand}
                      onChange={(e) => setNewLine((current) => ({ ...current, qty_demand: e.target.value }))}
                    />
                    <button onClick={addLine} disabled={!newLine.product_id || !newLine.location_id || !newLine.qty_demand} className="btn-primary px-3 text-[10px] font-bold uppercase tracking-wider">
                      Add Line
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button className="btn-ghost flex-1" onClick={() => setShowCreate(false)}>Cancel</button>
                <button className="btn-primary flex-1" disabled={!form.warehouse_id} onClick={submit}>
                  Create
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
