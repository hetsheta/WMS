import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { getStock, getProducts, getWarehouses, getLocations, adjustStock } from '../lib/api'
import toast from 'react-hot-toast'
import { SlidersHorizontal, X } from 'lucide-react'

const LOW_STOCK_THRESHOLD = 10

export default function Stock() {
  const qc = useQueryClient()
  const [warehouseId, setWarehouseId] = useState('')
  const [showLowStockOnly, setShowLowStockOnly] = useState(false)
  const [showAdjust, setShowAdjust] = useState(false)
  const [adj, setAdj] = useState({ warehouse_id: '', product_id: '', location_id: '', quantity: '' })

  const { data: stock = [], isLoading } = useQuery(
    ['stock', warehouseId],
    () => getStock(warehouseId ? { warehouse_id: warehouseId, limit: 200 } : { limit: 200 }).then((r) => r.data)
  )
  const { data: warehouses = [] } = useQuery('warehouses', () => getWarehouses().then((r) => r.data))
  const { data: products = [] } = useQuery('products-all', () => getProducts({ limit: 200 }).then((r) => r.data.items))
  const { data: adjustLocations = [] } = useQuery(
    ['stock-adjust-locations', adj.warehouse_id],
    () => getLocations(adj.warehouse_id).then((r) => r.data),
    { enabled: !!adj.warehouse_id }
  )

  const adjustMut = useMutation(adjustStock, {
    onSuccess: () => {
      toast.success('Stock adjusted')
      qc.invalidateQueries('stock')
      qc.invalidateQueries('dashboard')
      qc.invalidateQueries('dashboard-stock')
      qc.invalidateQueries('move-history')
      setShowAdjust(false)
      setAdj({ warehouse_id: '', product_id: '', location_id: '', quantity: '' })
    },
    onError: (e) => toast.error(e.response?.data?.detail ?? 'Failed'),
  })

  const visibleStock = showLowStockOnly
    ? stock.filter((item) => parseFloat(item.free_to_use) <= LOW_STOCK_THRESHOLD)
    : stock

  return (
    <div className="space-y-5 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Stock</h1>
          <p className="text-sm text-muted mt-0.5">On-hand inventory by location</p>
        </div>
        <button onClick={() => setShowAdjust(true)} className="btn-primary">
          <SlidersHorizontal size={15} /> Adjust
        </button>
      </div>

      <div className="flex gap-3 flex-wrap items-center">
        <select className="input max-w-xs" value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)}>
          <option value="">All warehouses</option>
          {warehouses.map((warehouse) => (
            <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm text-muted">
          <input
            type="checkbox"
            checked={showLowStockOnly}
            onChange={(e) => setShowLowStockOnly(e.target.checked)}
          />
          Show low stock only
        </label>
        <span className="text-xs text-muted">
          {visibleStock.filter((item) => parseFloat(item.free_to_use) <= LOW_STOCK_THRESHOLD).length} low stock items visible
        </span>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Location</th>
                <th>On hand</th>
                <th>Reserved</th>
                <th>Free to use</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && <tr><td colSpan={6} className="text-center text-muted py-10">Loading...</td></tr>}
              {!isLoading && visibleStock.length === 0 && (
                <tr><td colSpan={6} className="text-center text-muted py-10">No stock records</td></tr>
              )}
              {visibleStock.map((item) => {
                const lowStock = parseFloat(item.free_to_use) <= LOW_STOCK_THRESHOLD
                return (
                  <tr key={item.id} className={lowStock ? 'bg-danger/5' : ''}>
                    <td className="text-white font-medium">
                      <div className="flex items-center gap-2">
                        <span>{item.product?.name || item.product_id}</span>
                        {lowStock && <span className="badge bg-red-900/60 text-red-300">Low</span>}
                      </div>
                    </td>
                    <td className="font-mono text-xs text-muted">{item.location?.name || item.location_id}</td>
                    <td className="font-mono">{item.on_hand}</td>
                    <td className="font-mono text-amber-400">{item.reserved}</td>
                    <td className={`font-mono font-medium ${lowStock ? 'text-danger' : 'text-success'}`}>
                      {item.free_to_use}
                    </td>
                    <td className="text-muted text-xs">{new Date(item.updated_at).toLocaleString()}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {showAdjust && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="card w-full max-w-md">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-semibold text-white">Stock Adjustment</h2>
              <button onClick={() => setShowAdjust(false)} className="text-muted hover:text-white"><X size={18} /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="label">Warehouse</label>
                <select
                  className="input"
                  value={adj.warehouse_id}
                  onChange={(e) =>
                    setAdj((current) => ({
                      ...current,
                      warehouse_id: e.target.value,
                      location_id: '',
                    }))
                  }
                >
                  <option value="">Select warehouse...</option>
                  {warehouses.map((warehouse) => (
                    <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Product</label>
                <select
                  className="input"
                  value={adj.product_id}
                  onChange={(e) => setAdj((current) => ({ ...current, product_id: e.target.value }))}
                >
                  <option value="">Select product...</option>
                  {products.map((product) => (
                    <option key={product.id} value={product.id}>{product.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Location</label>
                <select
                  className="input"
                  value={adj.location_id}
                  onChange={(e) => setAdj((current) => ({ ...current, location_id: e.target.value }))}
                  disabled={!adj.warehouse_id}
                >
                  <option value="">Select location...</option>
                  {(adjustLocations ?? []).map((location) => (
                    <option key={location.id} value={location.id}>{location.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Quantity (+ to add, - to remove)</label>
                <input
                  type="number"
                  className="input"
                  placeholder="e.g. 10 or -5"
                  value={adj.quantity}
                  onChange={(e) => setAdj((current) => ({ ...current, quantity: e.target.value }))}
                />
              </div>
              <div className="flex gap-3 mt-2">
                <button className="btn-ghost flex-1" onClick={() => setShowAdjust(false)}>Cancel</button>
                <button
                  className="btn-primary flex-1"
                  disabled={!adj.product_id || !adj.location_id || adj.quantity === ''}
                  onClick={() =>
                    adjustMut.mutate({
                      product_id: adj.product_id,
                      location_id: adj.location_id,
                      quantity: parseFloat(adj.quantity),
                    })
                  }
                >
                  Apply
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
