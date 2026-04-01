import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { listInventories, getInventoryNodes } from '../api/inventories'
import { createJob, startJob } from '../api/triage'
import ModuleSelector, { DEFAULT_MODULES } from '../components/ModuleSelector'
import NodeStatusCard from '../components/NodeStatusCard'
import InventoryUploader from '../components/InventoryUploader'
import clsx from 'clsx'

const STEPS = ['Inventory', 'Nodes', 'Modules', 'Review']

export default function TriageNew() {
  const navigate = useNavigate()
  const location = useLocation()
  const locationState = location.state ?? {}

  const [step, setStep] = useState(0)
  const [invMode, setInvMode] = useState('existing') // existing | upload
  const [selectedInvId, setSelectedInvId] = useState(locationState.inventoryId ?? null)
  const [selectedNodes, setSelectedNodes] = useState(locationState.selectedNodes ?? [])
  const [modules, setModules] = useState(DEFAULT_MODULES)
  const [jobName, setJobName] = useState('')

  const { data: inventories = [] } = useQuery({
    queryKey: ['inventories'],
    queryFn: listInventories,
  })

  const { data: invNodes = [], isLoading: nodesLoading } = useQuery({
    queryKey: ['inventory-nodes', selectedInvId],
    queryFn: () => getInventoryNodes(selectedInvId),
    enabled: !!selectedInvId,
  })

  const { mutate: doCreate, isPending, isError, error } = useMutation({
    mutationFn: async () => {
      const job = await createJob({
        name: jobName || `Triage ${new Date().toLocaleString()}`,
        inventory_id: selectedInvId,
        selected_node_ids: selectedNodes.map((n) => n.id),
        selected_modules: modules,
      })
      await startJob(job.id)
      return job
    },
    onSuccess: (job) => navigate(`/triage/${job.id}`),
  })

  function toggleNode(node) {
    setSelectedNodes((prev) =>
      prev.some((n) => n.id === node.id) ? prev.filter((n) => n.id !== node.id) : [...prev, node]
    )
  }

  function selectAll() { setSelectedNodes(invNodes) }
  function clearAll() { setSelectedNodes([]) }

  function canNext() {
    if (step === 0) return !!selectedInvId
    if (step === 1) return selectedNodes.length > 0
    return true
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-xl font-bold text-gray-900">New Triage Job</h1>

      {/* Step indicator */}
      <div className="flex items-center gap-0">
        {STEPS.map((label, i) => (
          <div key={i} className="flex items-center flex-1">
            <div className={clsx(
              'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0',
              i < step ? 'bg-cyan-600 text-white' :
              i === step ? 'bg-cyan-600 text-white ring-4 ring-cyan-200' :
              'bg-gray-200 text-gray-500'
            )}>
              {i < step ? '✓' : i + 1}
            </div>
            <span className={clsx('ml-2 text-xs font-medium', i === step ? 'text-cyan-700' : 'text-gray-400')}>
              {label}
            </span>
            {i < STEPS.length - 1 && <div className="flex-1 h-px bg-gray-200 mx-3" />}
          </div>
        ))}
      </div>

      {/* Step content */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">

        {/* Step 0: Inventory */}
        {step === 0 && (
          <div className="space-y-4">
            <h2 className="text-base font-semibold text-gray-800">Select Inventory</h2>
            <div className="flex gap-3">
              <button
                onClick={() => setInvMode('existing')}
                className={clsx('px-4 py-2 text-sm rounded-md border', invMode === 'existing' ? 'border-cyan-500 bg-cyan-50 text-cyan-700' : 'border-gray-300 text-gray-600')}
              >
                Existing
              </button>
              <button
                onClick={() => setInvMode('upload')}
                className={clsx('px-4 py-2 text-sm rounded-md border', invMode === 'upload' ? 'border-cyan-500 bg-cyan-50 text-cyan-700' : 'border-gray-300 text-gray-600')}
              >
                Upload New
              </button>
            </div>

            {invMode === 'existing' ? (
              <div className="space-y-2">
                {inventories.length === 0 && (
                  <p className="text-sm text-gray-500">No inventories. Upload one first.</p>
                )}
                {inventories.map((inv) => (
                  <label key={inv.id} className={clsx(
                    'flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors',
                    selectedInvId === inv.id ? 'border-cyan-500 bg-cyan-50' : 'border-gray-200 hover:border-cyan-300'
                  )}>
                    <input
                      type="radio"
                      name="inventory"
                      className="accent-cyan-600"
                      checked={selectedInvId === inv.id}
                      onChange={() => { setSelectedInvId(inv.id); setSelectedNodes([]) }}
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-800">{inv.name}</p>
                      <p className="text-xs text-gray-400">{new Date(inv.created_at).toLocaleString()}</p>
                    </div>
                  </label>
                ))}
              </div>
            ) : (
              <InventoryUploader onUploaded={(inv) => {
                setSelectedInvId(inv.id)
                setInvMode('existing')
              }} />
            )}
          </div>
        )}

        {/* Step 1: Node selection */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-gray-800">Select Nodes</h2>
              <div className="flex gap-2">
                <button onClick={selectAll} className="text-xs text-cyan-600 hover:underline">Select all</button>
                <span className="text-gray-300">|</span>
                <button onClick={clearAll} className="text-xs text-gray-500 hover:underline">Clear</button>
              </div>
            </div>
            {nodesLoading ? (
              <p className="text-sm text-gray-500">Loading nodes…</p>
            ) : (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {invNodes.map((node) => (
                  <NodeStatusCard
                    key={node.id}
                    node={node}
                    selected={selectedNodes.some((n) => n.id === node.id)}
                    onToggle={toggleNode}
                  />
                ))}
              </div>
            )}
            {selectedNodes.length > 0 && (
              <p className="text-sm text-cyan-700 font-medium">{selectedNodes.length} node(s) selected</p>
            )}
          </div>
        )}

        {/* Step 2: Modules */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-base font-semibold text-gray-800">Select Collection Modules</h2>
            <ModuleSelector value={modules} onChange={setModules} />
          </div>
        )}

        {/* Step 3: Review */}
        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-base font-semibold text-gray-800">Review & Start</h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Job Name</label>
              <input
                type="text"
                placeholder={`Triage ${new Date().toLocaleString()}`}
                value={jobName}
                onChange={(e) => setJobName(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400"
              />
            </div>
            <div className="text-sm text-gray-700 space-y-1">
              <p><span className="font-medium">Inventory ID:</span> {selectedInvId}</p>
              <p><span className="font-medium">Nodes ({selectedNodes.length}):</span> {selectedNodes.map(n => n.ip_address).join(', ')}</p>
              <p><span className="font-medium">Modules enabled:</span>{' '}
                {Object.entries(modules).filter(([, v]) => v).map(([k]) => k.replace('collect_', '')).join(', ')}
              </p>
            </div>
            {isError && (
              <p className="text-sm text-red-600">{error?.response?.data?.detail ?? 'Failed to start job'}</p>
            )}
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={() => step > 0 ? setStep(step - 1) : navigate('/triage')}
          className="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
        >
          {step === 0 ? 'Cancel' : 'Back'}
        </button>
        {step < STEPS.length - 1 ? (
          <button
            onClick={() => setStep(step + 1)}
            disabled={!canNext()}
            className="px-4 py-2 text-sm bg-cyan-600 text-white rounded-md hover:bg-cyan-700 disabled:opacity-50"
          >
            Next
          </button>
        ) : (
          <button
            onClick={() => doCreate()}
            disabled={isPending}
            className="px-4 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {isPending ? 'Starting…' : 'Start Triage'}
          </button>
        )}
      </div>
    </div>
  )
}
