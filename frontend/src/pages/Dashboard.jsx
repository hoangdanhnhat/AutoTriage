import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { listInventories, getInventoryNodes, checkInventoryStatus } from '../api/inventories'
import NodeStatusCard from '../components/NodeStatusCard'
import { RefreshCw, Play } from 'lucide-react'

export default function Dashboard() {
  const [selectedInvId, setSelectedInvId] = useState(null)
  const [selectedNodes, setSelectedNodes] = useState([])
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: inventories = [] } = useQuery({
    queryKey: ['inventories'],
    queryFn: listInventories,
  })

  const { data: nodes = [], isLoading: nodesLoading } = useQuery({
    queryKey: ['inventory-nodes', selectedInvId],
    queryFn: () => getInventoryNodes(selectedInvId),
    enabled: !!selectedInvId,
  })

  const { mutate: checkStatus, isPending: checking } = useMutation({
    mutationFn: () => checkInventoryStatus(selectedInvId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['inventory-nodes', selectedInvId] }),
  })

  function toggleNode(node) {
    setSelectedNodes((prev) =>
      prev.some((n) => n.id === node.id) ? prev.filter((n) => n.id !== node.id) : [...prev, node]
    )
  }

  function startTriage() {
    navigate('/triage/new', { state: { selectedNodes, inventoryId: selectedInvId } })
  }

  const onlineCount = nodes.filter((n) => n.status === 'online').length
  const offlineCount = nodes.filter((n) => n.status === 'offline').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex gap-2">
          {selectedInvId && (
            <>
              <button
                onClick={() => checkStatus()}
                disabled={checking}
                className="flex items-center gap-2 px-3 py-2 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                <RefreshCw size={15} className={checking ? 'animate-spin' : ''} />
                {checking ? 'Checking…' : 'Check Status'}
              </button>
              {selectedNodes.length > 0 && (
                <button
                  onClick={startTriage}
                  className="flex items-center gap-2 px-3 py-2 text-sm bg-cyan-600 text-white rounded-md hover:bg-cyan-700"
                >
                  <Play size={15} />
                  Begin Triage ({selectedNodes.length})
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Inventory selector */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Active Inventory</label>
        <select
          value={selectedInvId ?? ''}
          onChange={(e) => { setSelectedInvId(Number(e.target.value) || null); setSelectedNodes([]) }}
          className="border border-gray-300 rounded-md px-3 py-2 text-sm w-full max-w-xs focus:outline-none focus:ring-2 focus:ring-cyan-400"
        >
          <option value="">— Select an inventory —</option>
          {inventories.map((inv) => (
            <option key={inv.id} value={inv.id}>{inv.name}</option>
          ))}
        </select>
      </div>

      {/* Stats */}
      {selectedInvId && nodes.length > 0 && (
        <div className="flex gap-4">
          <Stat label="Total Nodes" value={nodes.length} color="text-gray-700" />
          <Stat label="Online" value={onlineCount} color="text-green-600" />
          <Stat label="Offline" value={offlineCount} color="text-red-600" />
          <Stat label="Selected" value={selectedNodes.length} color="text-cyan-600" />
        </div>
      )}

      {/* Node grid */}
      {selectedInvId && (
        nodesLoading ? (
          <p className="text-sm text-gray-500">Loading nodes…</p>
        ) : nodes.length === 0 ? (
          <p className="text-sm text-gray-500">No nodes in this inventory.</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {nodes.map((node) => (
              <NodeStatusCard
                key={node.id}
                node={node}
                selected={selectedNodes.some((n) => n.id === node.id)}
                onToggle={toggleNode}
              />
            ))}
          </div>
        )
      )}

      {!selectedInvId && (
        <div className="bg-white rounded-lg border border-dashed border-gray-300 p-10 text-center">
          <p className="text-gray-400 text-sm">Select an inventory to view nodes</p>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value, color }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 px-5 py-3 min-w-[100px] text-center">
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}
