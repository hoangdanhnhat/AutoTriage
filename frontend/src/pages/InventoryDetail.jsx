import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getInventory, getInventoryNodes, checkInventoryStatus } from '../api/inventories'
import { ArrowLeft, Play, RefreshCw } from 'lucide-react'
import clsx from 'clsx'

const statusDot = {
  online:  'bg-emerald-500',
  offline: 'bg-rose-500',
  unknown: 'bg-slate-400',
}

const statusPill = {
  online: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  offline: 'bg-rose-50 text-rose-700 ring-rose-200',
  unknown: 'bg-slate-100 text-slate-600 ring-slate-200',
}

export default function InventoryDetail() {
  const { id } = useParams()
  const invId = Number(id)
  const qc = useQueryClient()
  const navigate = useNavigate()

  const { data: inv } = useQuery({
    queryKey: ['inventory', invId],
    queryFn: () => getInventory(invId),
  })

  const { data: nodes = [], isLoading } = useQuery({
    queryKey: ['inventory-nodes', invId],
    queryFn: () => getInventoryNodes(invId),
  })

  const { mutate: checkStatus, isPending: checking } = useMutation({
    mutationFn: () => checkInventoryStatus(invId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['inventory-nodes', invId] }),
  })

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <Link to="/inventories" className="muted-link mb-3 text-slate-500">
            <ArrowLeft size={16} />
            Inventories
          </Link>
          <p className="page-kicker">Inventory</p>
          <h1 className="page-title">{inv?.name ?? 'Inventory'}</h1>
          <p className="page-subtitle">{nodes.length} nodes available for status checks and triage collection.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => checkStatus()}
            disabled={checking}
            className="btn-secondary"
          >
            <RefreshCw size={16} className={checking ? 'animate-spin' : ''} />
            {checking ? 'Checking...' : 'Check Status'}
          </button>
          <button
            onClick={() => navigate('/triage/new', { state: { inventoryId: invId } })}
            className="btn-primary"
          >
            <Play size={16} />
            Begin Triage
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="surface p-6 text-sm text-slate-500">Loading...</div>
      ) : (
        <div className="table-shell overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="table-head">
              <tr>
                <th className="px-4 py-3 text-left">IP Address</th>
                <th className="px-4 py-3 text-left">Hostname</th>
                <th className="px-4 py-3 text-left">Group</th>
                <th className="px-4 py-3 text-left">User</th>
                <th className="px-4 py-3 text-left">Connection</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Last Checked</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {nodes.map((n) => (
                <tr key={n.id} className="table-row">
                  <td className="px-4 py-3">
                    <span className="mono-value">{n.ip_address}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{n.hostname ?? '-'}</td>
                  <td className="px-4 py-3 text-slate-600">{n.group_name ?? '-'}</td>
                  <td className="px-4 py-3 text-slate-600">{n.ansible_user ?? '-'}</td>
                  <td className="px-4 py-3 text-slate-600">{n.ansible_connection ?? 'ssh'}</td>
                  <td className="px-4 py-3">
                    <span className={clsx('status-pill ring-1', statusPill[n.status] ?? statusPill.unknown)}>
                      <span className={clsx('h-2 w-2 rounded-full', statusDot[n.status] ?? statusDot.unknown)} />
                      {n.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400">
                    {n.last_checked ? new Date(n.last_checked).toLocaleTimeString() : '-'}
                  </td>
                </tr>
              ))}
              {nodes.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-sm text-slate-400">No nodes</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
