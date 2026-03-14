import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { getProducts, createProduct, updateProduct } from '../lib/api'
import toast from 'react-hot-toast'
import { Plus, X, Search, Pencil } from 'lucide-react'

export default function Products() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ name: '', sku: '', category: '', description: '', unit_of_measure: 'pcs', cost_price: '' })

  const { data, isLoading } = useQuery(
    ['products', search],
    () => getProducts({ search: search || undefined, limit: 100 }).then(r => r.data),
    { keepPreviousData: true }
  )

  const createMut = useMutation(createProduct, {
    onSuccess: () => { toast.success('Product created'); qc.invalidateQueries('products'); close() },
    onError: (e) => toast.error(e.response?.data?.detail ?? 'Failed'),
  })
  const updateMut = useMutation(({ id, data }) => updateProduct(id, data), {
    onSuccess: () => { toast.success('Product updated'); qc.invalidateQueries('products'); close() },
    onError: (e) => toast.error(e.response?.data?.detail ?? 'Failed'),
  })

  const close = () => { setShowForm(false); setEditing(null); setForm({ name: '', sku: '', category: '', description: '', unit_of_measure: 'pcs', cost_price: '' }) }
  const openEdit = (p) => { setEditing(p); setForm({ name: p.name, sku: p.sku, category: p.category || '', description: p.description || '', unit_of_measure: p.unit_of_measure, cost_price: p.cost_price }); setShowForm(true) }

  const submit = () => {
    const payload = { ...form, cost_price: parseFloat(form.cost_price) || 0 }
    if (!payload.category) delete payload.category
    if (editing) updateMut.mutate({ id: editing.id, data: payload })
    else createMut.mutate(payload)
  }

  const products = data?.items ?? []

  return (
    <div className="space-y-5 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Products</h1>
          <p className="text-sm text-muted mt-0.5">{data?.total ?? 0} products</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary"><Plus size={15} /> Add product</button>
      </div>

      {/* Search */}
      <div className="relative max-w-xs">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
        <input className="input pl-8" placeholder="Search by name or SKU..."
          value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr><th>Name</th><th>SKU</th><th>Category</th><th>UOM</th><th>Cost price</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {isLoading && <tr><td colSpan={7} className="text-center text-muted py-10">Loading...</td></tr>} 
              {products.map(p => (
                <tr key={p.id}>
                  <td className="text-white font-medium">{p.name}</td>
                  <td className="font-mono text-xs text-accent-light">{p.sku}</td>
                  <td className="text-muted text-xs">{p.category || '—'}</td>
                  <td className="text-muted">{p.unit_of_measure}</td>
                  <td className="font-mono">₹{p.cost_price}</td>
                  <td>
                    <span className={p.is_active ? 'badge bg-green-900/60 text-green-300' : 'badge bg-red-900/60 text-red-400'}>
                      {p.is_active ? 'active' : 'inactive'}
                    </span>
                  </td>
                  <td>
                    <button onClick={() => openEdit(p)} className="text-muted hover:text-white p-1">
                      <Pencil size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Form modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="card w-full max-w-md">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-semibold text-white">{editing ? 'Edit product' : 'New product'}</h2>
              <button onClick={close} className="text-muted hover:text-white"><X size={18} /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="label">Name</label>
                <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">SKU</label>
                  <input className="input font-mono" value={form.sku} disabled={!!editing}
                    onChange={e => setForm(f => ({ ...f, sku: e.target.value }))} />
                </div>
                <div>
                  <label className="label">Category</label>
                  <input className="input" placeholder="e.g. Electronics" value={form.category}
                    onChange={e => setForm(f => ({ ...f, category: e.target.value }))} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Unit</label>
                  <input className="input" value={form.unit_of_measure}
                    onChange={e => setForm(f => ({ ...f, unit_of_measure: e.target.value }))} />
                </div>
                <div>
                  <label className="label">Cost price</label>
                  <input type="number" className="input" value={form.cost_price}
                    onChange={e => setForm(f => ({ ...f, cost_price: e.target.value }))} />
                </div>
              </div>
              <div>
                <label className="label">Description</label>
                <textarea className="input resize-none" rows={2} value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
              </div>
              <div className="flex gap-3 pt-1">
                <button className="btn-ghost flex-1" onClick={close}>Cancel</button>
                <button className="btn-primary flex-1" onClick={submit}>
                  {editing ? 'Save' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
