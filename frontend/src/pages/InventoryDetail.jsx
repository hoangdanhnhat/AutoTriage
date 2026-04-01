import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getInventory, getInventoryNodes, checkInventoryStatus } from '../api/inventories'
import { RefreshCw, ArrowLeft, Play } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import clsx from 'clsx'

const statusDot = {
  online:  'bg-green-500',
  offline: 'bg-red-500',
  unknown: 'bg-gray-400',
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
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <Link to="/inventories" className="text-gray-400 hover:text-gray-600">
          <ArrowLeft size={20} />
        </Link>
        <h1 className="text-xl font-bold text-gray-900">{inv?.name ?? 'Inventory'}</h1>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => checkStatus()}
          disabled={checking}
          className="flex items-center gap-2 px-3 py-2 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw size={15} className={checking ? 'animate-spin' : ''} />
          {checking ? 'Checking…' : 'Check Status'}
        </button>
        <button
          onClick={() => navigate('/triage/new', { state: { inventoryId: invId } })}
          className="flex items-center gap-2 px-3 py-2 text-sm bg-cyan-600 text-white rounded-md hover:bg-cyan-700"
        >
          <Play size={15} />
          Begin Triage
        </button>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
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
            <tbody className="divide-y divide-gray-100">
              {nodes.map((n) => (
                <tr key={n.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono">{n.ip_address}</td>
                  <td className="px-4 py-3 text-gray-600">{n.hostname ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{n.group_name ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{n.ansible_user ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{n.ansible_connection ?? 'ssh'}</td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-1.5">
                      <span className={clsx('w-2 h-2 rounded-full', statusDot[n.status] ?? statusDot.unknown)} />
                      <span className="capitalize text-xs">{n.status}</span>
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {n.last_checked ? new Date(n.last_checked).toLocaleTimeString() : '—'}
                  </td>
                </tr>
              ))}
              {nodes.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-gray-400 text-sm">No nodes</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
