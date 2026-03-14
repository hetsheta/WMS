import React, { useState } from 'react'
import { useQuery } from 'react-query'
import { format } from 'date-fns'
import { getMoveHistory } from '../lib/api'

const TYPES = ['', 'receipt', 'delivery', 'internal', 'adjustment']

export default function History() {
  const [filters, setFilters] = useState({ q: '', op_type: '' })

  const { data, isLoading } = useQuery(
    ['move-history', filters],
    () => {
      const params = { ...filters, limit: 100 }
      Object.keys(params).forEach((key) => {
        if (!params[key]) delete params[key]
      })
      return getMoveHistory(params).then((r) => r.data)
    },
    { keepPreviousData: true }
  )

  const moves = data?.items ?? []

  return (
    <div className="space-y-5 max-w-6xl">
      <div>
        <h1 className="text-2xl font-semibold text-white">Move History</h1>
        <p className="text-sm text-muted mt-0.5">Stock ledger and operation logs</p>
      </div>

      <div className="flex gap-3">
        <input
          className="input max-w-sm"
          value={filters.q}
          onChange={(e) => setFilters((current) => ({ ...current, q: e.target.value }))}
          placeholder="Search by reference, product, SKU, or location"
        />
        <select
          className="input max-w-[180px]"
          value={filters.op_type}
          onChange={(e) => setFilters((current) => ({ ...current, op_type: e.target.value }))}
        >
          {TYPES.map((type) => (
            <option key={type} value={type}>
              {type || 'All types'}
            </option>
          ))}
        </select>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Operation</th>
                <th>Product</th>
                <th>From</th>
                <th>To</th>
                <th>Quantity</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && <tr><td colSpan={6} className="text-center text-muted py-10">Loading...</td></tr>}
              {!isLoading && moves.length === 0 && (
                <tr><td colSpan={6} className="text-center text-muted py-10">No history found</td></tr>
              )}
              {moves.map((move) => (
                <tr key={move.id}>
                  <td className="text-muted text-xs">
                    {move.done_at
                      ? format(new Date(move.done_at), 'MMM d, HH:mm')
                      : format(new Date(move.created_at), 'MMM d, HH:mm')}
                  </td>
                  <td>
                    <div className="flex flex-col">
                      <span className="font-mono text-accent-light text-xs">{move.reference}</span>
                      <span className="text-[10px] text-muted uppercase">{move.operation_type}</span>
                    </div>
                  </td>
                  <td className="text-white font-medium">{move.product?.name || move.product_id}</td>
                  <td className="text-muted text-xs">{move.location?.name || move.location_id}</td>
                  <td className="text-muted text-xs">{move.dest_location?.name || '—'}</td>
                  <td className="font-mono">{move.qty_done}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
