import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { getOperation, validateOperation, markReady, confirmOperation, cancelOperation } from '../lib/api'
import toast from 'react-hot-toast'
import { ArrowLeft, CheckCircle2, Play, PackageCheck, XCircle, ArrowRight, Printer } from 'lucide-react'
import { format } from 'date-fns'

export default function OperationDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [doneQuantities, setDoneQuantities] = useState({})

  const { data: op, isLoading } = useQuery(['operation', id], () => getOperation(id).then((r) => r.data))

  useEffect(() => {
    if (!op) return
    const next = {}
    op.move_lines.forEach((line) => {
      next[line.id] = line.qty_done > 0 ? String(line.qty_done) : String(line.qty_demand)
    })
    setDoneQuantities(next)
  }, [op])

  const mutOpts = {
    onSuccess: () => {
      toast.success('Updated')
      qc.invalidateQueries(['operation', id])
      qc.invalidateQueries('operations')
      qc.invalidateQueries('recent-ops')
      qc.invalidateQueries('dashboard')
      qc.invalidateQueries('move-history')
      qc.invalidateQueries('stock')
    },
    onError: (e) => toast.error(e.response?.data?.detail ?? 'Failed'),
  }

  const validateMut = useMutation(() => validateOperation(id), mutOpts)
  const readyMut = useMutation(() => markReady(id), mutOpts)
  const cancelMut = useMutation(() => cancelOperation(id), mutOpts)
  const confirmMut = useMutation(() => {
    const quantities = {}
    op.move_lines.forEach((line) => {
      const raw = doneQuantities[line.id]
      quantities[line.id] = raw === '' || raw == null ? parseFloat(line.qty_demand) : parseFloat(raw)
    })
    return confirmOperation(id, quantities)
  }, mutOpts)

  if (isLoading) return <div className="text-muted p-8 text-center">Loading...</div>
  if (!op) return <div className="text-muted p-8 text-center">Not found</div>

  const isDone = op.status === 'done'
  const isCancelled = op.status === 'cancelled'
  const frozen = isDone || isCancelled
  const partnerLabel = op.operation_type === 'receipt' ? 'Supplier' : op.operation_type === 'delivery' ? 'Customer' : 'Party'
  const referenceLabel = op.operation_type === 'receipt' ? 'Receipt Ref' : op.operation_type === 'delivery' ? 'Order Ref' : 'External Ref'

  return (
    <div className="space-y-5 max-w-4xl print-surface">
      <div className="flex items-start gap-4 no-print">
        <button onClick={() => navigate('/operations')} className="btn-ghost px-2.5 py-2 mt-0.5">
          <ArrowLeft size={16} />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-semibold text-white font-mono">{op.reference}</h1>
            <span className={`badge-${op.operation_type}`}>{op.operation_type}</span>
            <span className={`badge-${op.status}`}>{op.status}</span>
          </div>
          <p className="text-sm text-muted mt-1">Created {format(new Date(op.created_at), 'MMM d, yyyy HH:mm')}</p>
        </div>
        <button onClick={() => window.print()} className="btn-ghost">
          <Printer size={15} /> Print
        </button>
      </div>

      {!frozen && (
        <div className="card flex flex-wrap gap-2 no-print">
          {op.status === 'draft' && (
            <button className="btn-primary" onClick={() => validateMut.mutate()}>
              <CheckCircle2 size={15} /> Validate
            </button>
          )}
          {op.status === 'validated' && (
            <button className="btn-primary" onClick={() => readyMut.mutate()}>
              <Play size={15} /> Mark Ready
            </button>
          )}
          {op.status === 'ready' && (
            <button className="btn-primary" onClick={() => confirmMut.mutate()}>
              <PackageCheck size={15} /> Confirm Done
            </button>
          )}
          <button className="btn-danger" onClick={() => cancelMut.mutate()}>
            <XCircle size={15} /> Cancel
          </button>
        </div>
      )}

      <div className="card">
        <h2 className="text-sm font-medium text-white mb-4">Details</h2>
        <div className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <div>
            <span className="text-muted">Warehouse</span>
            <p className="text-slate-300 font-mono text-xs mt-0.5">{op.warehouse_id}</p>
          </div>
          <div>
            <span className="text-muted">Scheduled</span>
            <p className="text-slate-300 mt-0.5">
              {op.scheduled_date ? format(new Date(op.scheduled_date), 'MMM d, yyyy') : '—'}
            </p>
          </div>
          {op.partner_name && (
            <div>
              <span className="text-muted">{partnerLabel}</span>
              <p className="text-slate-300 mt-0.5">{op.partner_name}</p>
            </div>
          )}
          {op.external_reference && (
            <div>
              <span className="text-muted">{referenceLabel}</span>
              <p className="text-slate-300 font-mono text-xs mt-0.5">{op.external_reference}</p>
            </div>
          )}
          {op.responsible_name && (
            <div>
              <span className="text-muted">Responsible</span>
              <p className="text-slate-300 mt-0.5">{op.responsible_name}</p>
            </div>
          )}
          {op.effective_date && (
            <div>
              <span className="text-muted">Completed</span>
              <p className="text-slate-300 mt-0.5">{format(new Date(op.effective_date), 'MMM d, yyyy HH:mm')}</p>
            </div>
          )}
          {op.notes && (
            <div className="col-span-2">
              <span className="text-muted">Notes</span>
              <p className="text-slate-300 mt-0.5">{op.notes}</p>
            </div>
          )}
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-border">
          <h2 className="text-sm font-medium text-white">Product Lines</h2>
        </div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Location</th>
                <th>Qty demand</th>
                <th>Qty done</th>
                <th>State</th>
              </tr>
            </thead>
            <tbody>
              {op.move_lines.length === 0 && (
                <tr><td colSpan={5} className="text-center text-muted py-8">No lines</td></tr>
              )}
              {op.move_lines.map((line) => (
                <tr key={line.id}>
                  <td className="text-white font-medium">{line.product?.name || line.product_id}</td>
                  <td className="text-muted text-xs">
                    <div className="flex items-center gap-1">
                      <span>{line.location?.name || line.location_id}</span>
                      {op.operation_type === 'internal' && line.dest_location_id && (
                        <>
                          <ArrowRight size={12} className="text-accent" />
                          <span>{line.dest_location?.name || line.dest_location_id}</span>
                        </>
                      )}
                    </div>
                  </td>
                  <td className="font-mono">{line.qty_demand}</td>
                  <td>
                    {op.status === 'ready' ? (
                      <input
                        type="number"
                        min="0"
                        step="0.0001"
                        className="input max-w-[120px] py-1.5 text-sm no-print"
                        value={doneQuantities[line.id] ?? ''}
                        onChange={(e) =>
                          setDoneQuantities((current) => ({ ...current, [line.id]: e.target.value }))
                        }
                      />
                    ) : (
                      <span className={`font-mono ${line.qty_done > 0 ? 'text-success' : 'text-muted'}`}>
                        {line.qty_done}
                      </span>
                    )}
                    {op.status === 'ready' && (
                      <span className="hidden print:inline font-mono">{doneQuantities[line.id] ?? line.qty_demand}</span>
                    )}
                  </td>
                  <td><span className={`badge-${line.state}`}>{line.state}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
