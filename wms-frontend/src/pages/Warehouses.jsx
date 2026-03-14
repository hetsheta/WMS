import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { getWarehouses, createWarehouse, getLocations, createLocation } from '../lib/api'
import toast from 'react-hot-toast'
import { Plus, X, ChevronDown, ChevronRight, MapPin } from 'lucide-react'

function LocationsPanel({ warehouseId }) {
  const qc = useQueryClient()
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ name: '', short_code: '', barcode: '' })

  const { data: locs = [] } = useQuery(['locations', warehouseId], () => getLocations(warehouseId).then(r => r.data))

  const addMut = useMutation((data) => createLocation(warehouseId, data), {
    onSuccess: () => { toast.success('Location added'); qc.invalidateQueries(['locations', warehouseId]); setShowAdd(false); setForm({ name: '', short_code: '', barcode: '' }) },
    onError: (e) => toast.error(e.response?.data?.detail ?? 'Failed'),
  })

  return (
    <div className="mt-3 pl-4 border-l border-border space-y-2">
      {locs.map(l => (
        <div key={l.id} className="flex items-center gap-2 text-sm">
          <MapPin size={12} className="text-muted" />
          <span className="text-slate-300">{l.name}</span>
          <span className="font-mono text-xs text-muted">({l.short_code})</span>
          {l.barcode && <span className="font-mono text-xs text-muted">{l.barcode}</span>}
        </div>
      ))}
      {showAdd ? (
        <div className="flex gap-2 flex-wrap">
          <input className="input text-xs max-w-[140px]" placeholder="Name" value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          <input className="input text-xs max-w-[80px]" placeholder="Code" value={form.short_code}
            onChange={e => setForm(f => ({ ...f, short_code: e.target.value }))} />
          <input className="input text-xs max-w-[120px]" placeholder="Barcode (opt)" value={form.barcode}
            onChange={e => setForm(f => ({ ...f, barcode: e.target.value }))} />
          <button className="btn-primary text-xs px-3" onClick={() => addMut.mutate(form)}>Add</button>
          <button className="btn-ghost text-xs px-3" onClick={() => setShowAdd(false)}>Cancel</button>
        </div>
      ) : (
        <button onClick={() => setShowAdd(true)} className="flex items-center gap-1 text-xs text-muted hover:text-accent-light">
          <Plus size={12} /> Add location
        </button>
      )}
    </div>
  )
}

export default function Warehouses() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [expanded, setExpanded] = useState({})
  const [form, setForm] = useState({ name: '', short_code: '', address: '' })

  const { data: warehouses = [], isLoading } = useQuery('warehouses', () => getWarehouses().then(r => r.data))

  const createMut = useMutation(createWarehouse, {
    onSuccess: () => { toast.success('Warehouse created'); qc.invalidateQueries('warehouses'); setShowForm(false); setForm({ name: '', short_code: '', address: '' }) },
    onError: (e) => toast.error(e.response?.data?.detail ?? 'Failed'),
  })

  const toggle = (id) => setExpanded(e => ({ ...e, [id]: !e[id] }))

  return (
    <div className="space-y-5 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Warehouses</h1>
          <p className="text-sm text-muted mt-0.5">Facilities and storage locations</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary"><Plus size={15} /> Add warehouse</button>
      </div>

      <div className="space-y-3">
        {isLoading && <p className="text-muted text-sm">Loading…</p>}
        {warehouses.map(wh => (
          <div key={wh.id} className="card">
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => toggle(wh.id)}>
              <button className="text-muted">
                {expanded[wh.id] ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-white">{wh.name}</span>
                  <span className="font-mono text-xs text-accent-light bg-accent/10 px-1.5 py-0.5 rounded">{wh.short_code}</span>
                  {!wh.is_active && <span className="badge bg-red-900/60 text-red-400">inactive</span>}
                </div>
                {wh.address && <p className="text-xs text-muted mt-0.5">{wh.address}</p>}
              </div>
            </div>
            {expanded[wh.id] && <LocationsPanel warehouseId={wh.id} />}
          </div>
        ))}
      </div>

      {/* Form modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="card w-full max-w-md">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-semibold text-white">New Warehouse</h2>
              <button onClick={() => setShowForm(false)} className="text-muted hover:text-white"><X size={18} /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="label">Name</label>
                <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              </div>
              <div>
                <label className="label">Short code</label>
                <input className="input font-mono uppercase" value={form.short_code}
                  onChange={e => setForm(f => ({ ...f, short_code: e.target.value.toUpperCase() }))} />
              </div>
              <div>
                <label className="label">Address</label>
                <textarea className="input resize-none" rows={2} value={form.address}
                  onChange={e => setForm(f => ({ ...f, address: e.target.value }))} />
              </div>
              <div className="flex gap-3 pt-1">
                <button className="btn-ghost flex-1" onClick={() => setShowForm(false)}>Cancel</button>
                <button className="btn-primary flex-1" onClick={() => createMut.mutate(form)}>Create</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
