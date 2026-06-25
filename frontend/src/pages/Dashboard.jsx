import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { listInventories, getInventoryNodes, checkInventoryStatus } from '../api/inventories'
import NodeStatusCard from '../components/NodeStatusCard'
import { Activity, Database, Play, RefreshCw, Server } from 'lucide-react'

export default function Dashboard() {
  const [selectedInvId, setSelectedInvId] = useState(null)
  const [selectedNodes, setSelectedNodes] = useState([])
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: inventories = [] } = useQuery({
    queryKey: ['inventories'],
    queryFn: listInventories,
  })

  useEffect(() => {
    if (inventories.length === 1 && !selectedInvId) {
      setSelectedInvId(inventories[0].id)
      setSelectedNodes([])
    }
  }, [inventories, selectedInvId])

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
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="page-kicker">Operations</p>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">
            {inventories.length === 1
              ? 'Check host reachability, select target nodes, then launch triage.'
              : 'Select an inventory, check host reachability, then launch triage for the nodes that matter.'}
          </p>
        </div>
        {selectedInvId && (
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => checkStatus()}
              disabled={checking}
              className="btn-secondary"
            >
              <RefreshCw size={16} className={checking ? 'animate-spin' : ''} />
              {checking ? 'Checking...' : 'Check Status'}
            </button>
            {selectedNodes.length > 0 && (
              <button onClick={startTriage} className="btn-primary">
                <Play size={16} />
                Begin Triage ({selectedNodes.length})
              </button>
            )}
          </div>
        )}
      </div>

      <section className="surface p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-xl">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
              <Database size={17} className="text-teal-700" />
              Active Inventory
            </div>
            <p className="mt-1 text-sm text-slate-500">Node status and selections are scoped to the selected inventory.</p>
          </div>
          {inventories.length === 1 ? (
            <div className="max-w-sm rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-800">
              {inventories[0].name}
            </div>
          ) : (
            <select
              value={selectedInvId ?? ''}
              onChange={(e) => { setSelectedInvId(Number(e.target.value) || null); setSelectedNodes([]) }}
              className="select-field max-w-sm"
            >
              <option value="">Select an inventory</option>
              {inventories.map((inv) => (
                <option key={inv.id} value={inv.id}>{inv.name}</option>
              ))}
            </select>
          )}
        </div>
      </section>

      {selectedInvId && nodes.length > 0 && (
        <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Stat label="Total Nodes" value={nodes.length} icon={Server} tone="slate" />
          <Stat label="Online" value={onlineCount} icon={Activity} tone="emerald" />
          <Stat label="Offline" value={offlineCount} icon={Activity} tone="rose" />
          <Stat label="Selected" value={selectedNodes.length} icon={Play} tone="teal" />
        </section>
      )}

      {selectedInvId ? (
        nodesLoading ? (
          <div className="surface p-6 text-sm text-slate-500">Loading nodes...</div>
        ) : nodes.length === 0 ? (
          <div className="empty-state">No nodes in this inventory.</div>
        ) : (
          <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-5">
            {nodes.map((node) => (
              <NodeStatusCard
                key={node.id}
                node={node}
                selected={selectedNodes.some((n) => n.id === node.id)}
                onToggle={toggleNode}
              />
            ))}
          </section>
        )
      ) : (
        <div className="empty-state">Select an inventory to view nodes.</div>
      )}
    </div>
  )
}

function Stat({ label, value, icon: Icon, tone }) {
  const toneClass = {
    slate: 'bg-slate-100 text-slate-700',
    emerald: 'bg-emerald-50 text-emerald-700',
    rose: 'bg-rose-50 text-rose-700',
    teal: 'bg-teal-50 text-teal-700',
  }[tone]

  return (
    <div className="surface flex items-center justify-between p-4">
      <div>
        <p className="text-xs font-semibold uppercase text-slate-400">{label}</p>
        <p className="mt-1 text-2xl font-semibold text-slate-950">{value}</p>
      </div>
      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${toneClass}`}>
        <Icon size={18} />
      </div>
    </div>
  )
}
