import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { listInventories, getInventoryNodes } from '../api/inventories'
import { createJob, startJob } from '../api/triage'
import ModuleSelector, { DEFAULT_MODULES, MODULE_LABELS } from '../components/ModuleSelector'
import NodeStatusCard from '../components/NodeStatusCard'
import InventoryUploader from '../components/InventoryUploader'
import { Check, ChevronLeft, ChevronRight, Database, Play } from 'lucide-react'
import clsx from 'clsx'

const STEPS = ['Inventory', 'Nodes', 'Modules', 'Review']

export default function TriageNew() {
  const navigate = useNavigate()
  const location = useLocation()
  const locationState = location.state ?? {}
  const hasPreselectedNodes = !!locationState.inventoryId && (locationState.selectedNodes?.length ?? 0) > 0

  const [step, setStep] = useState(hasPreselectedNodes ? 2 : 0)
  const [invMode, setInvMode] = useState('existing')
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

  const enabledModules = Object.entries(modules)
    .filter(([, v]) => v)
    .map(([k]) => MODULE_LABELS[k] ?? k.replace('collect_', ''))

  return (
    <div className="page-stack max-w-5xl">
      <div className="page-header">
        <div>
          <p className="page-kicker">New collection</p>
          <h1 className="page-title">New Triage Job</h1>
          <p className="page-subtitle">Build a focused collection plan and start it against selected nodes.</p>
        </div>
      </div>

      <StepIndicator step={step} />

      <section className="surface p-5 sm:p-6">
        {step === 0 && (
          <div className="space-y-5">
            <StepHeading title="Select Inventory" subtitle="Use an existing inventory or upload a new one before choosing target nodes." />
            <div className="inline-flex rounded-lg bg-slate-100 p-1">
              <button
                onClick={() => setInvMode('existing')}
                className={clsx('rounded-md px-3 py-2 text-sm font-semibold transition-all', invMode === 'existing' ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-900')}
              >
                Existing
              </button>
              <button
                onClick={() => setInvMode('upload')}
                className={clsx('rounded-md px-3 py-2 text-sm font-semibold transition-all', invMode === 'upload' ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-900')}
              >
                Upload New
              </button>
            </div>

            {invMode === 'existing' ? (
              <div className="grid gap-3">
                {inventories.length === 0 && (
                  <p className="text-sm text-slate-500">No inventories. Upload one first.</p>
                )}
                {inventories.map((inv) => (
                  <label
                    key={inv.id}
                    className={clsx(
                      'group flex cursor-pointer items-center gap-3 rounded-lg border p-4 transition-all duration-200',
                      selectedInvId === inv.id
                        ? 'border-teal-400 bg-teal-50/70 ring-4 ring-teal-100'
                        : 'border-slate-200 bg-white/80 hover:-translate-y-0.5 hover:border-teal-300'
                    )}
                  >
                    <input
                      type="radio"
                      name="inventory"
                      className="accent-teal-600"
                      checked={selectedInvId === inv.id}
                      onChange={() => { setSelectedInvId(inv.id); setSelectedNodes([]) }}
                    />
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-slate-600 group-hover:bg-teal-50 group-hover:text-teal-700">
                      <Database size={18} />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-slate-900">{inv.name}</p>
                      <p className="mt-0.5 text-xs text-slate-400">{new Date(inv.created_at).toLocaleString()}</p>
                    </div>
                  </label>
                ))}
              </div>
            ) : (
              <InventoryUploader onUploaded={(inv) => {
                setSelectedInvId(inv.id)
                setSelectedNodes([])
                setInvMode('existing')
              }} />
            )}
          </div>
        )}

        {step === 1 && (
          <div className="space-y-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <StepHeading title="Select Nodes" subtitle={`${selectedNodes.length} of ${invNodes.length} nodes selected.`} />
              <div className="flex gap-2">
                <button onClick={selectAll} className="btn-secondary h-9">Select all</button>
                <button onClick={clearAll} className="btn-ghost h-9">Clear</button>
              </div>
            </div>
            {nodesLoading ? (
              <p className="text-sm text-slate-500">Loading nodes...</p>
            ) : invNodes.length === 0 ? (
              <div className="empty-state">No nodes in this inventory.</div>
            ) : (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
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
          </div>
        )}

        {step === 2 && (
          <div className="space-y-5">
            <StepHeading title="Select Collection Modules" subtitle="Enable the modules required for this collection run." />
            <ModuleSelector value={modules} onChange={setModules} />
          </div>
        )}

        {step === 3 && (
          <div className="space-y-5">
            <StepHeading title="Review and Start" subtitle="Name the job and confirm the inventory, nodes, and modules." />
            <div>
              <label className="mb-1.5 block text-sm font-semibold text-slate-700">Job Name</label>
              <input
                type="text"
                placeholder={`Triage ${new Date().toLocaleString()}`}
                value={jobName}
                onChange={(e) => setJobName(e.target.value)}
                className="input-field"
              />
            </div>
            <div className="grid gap-3 lg:grid-cols-3">
              <ReviewItem label="Inventory ID" value={selectedInvId} />
              <ReviewItem label="Nodes" value={selectedNodes.length} />
              <ReviewItem label="Modules" value={enabledModules.length} />
            </div>
            <div className="surface-muted p-4 text-sm leading-6 text-slate-600">
              <p><span className="font-semibold text-slate-800">Targets:</span> {selectedNodes.map(n => n.ip_address).join(', ')}</p>
              <p><span className="font-semibold text-slate-800">Modules:</span> {enabledModules.join(', ') || 'None selected'}</p>
            </div>
            {isError && (
              <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
                {error?.response?.data?.detail ?? 'Failed to start job'}
              </p>
            )}
          </div>
        )}
      </section>

      <div className="flex justify-between">
        <button
          onClick={() => step > 0 ? setStep(step - 1) : navigate('/triage')}
          className="btn-secondary"
        >
          <ChevronLeft size={16} />
          {step === 0 ? 'Cancel' : 'Back'}
        </button>
        {step < STEPS.length - 1 ? (
          <button
            onClick={() => setStep(step + 1)}
            disabled={!canNext()}
            className="btn-primary"
          >
            Next
            <ChevronRight size={16} />
          </button>
        ) : (
          <button
            onClick={() => doCreate()}
            disabled={isPending}
            className="btn-success"
          >
            <Play size={16} />
            {isPending ? 'Starting...' : 'Start Triage'}
          </button>
        )}
      </div>
    </div>
  )
}

function StepIndicator({ step }) {
  return (
    <div className="surface px-4 py-3">
      <div className="grid gap-2 sm:grid-cols-4">
        {STEPS.map((label, i) => (
          <div
            key={label}
            className={clsx(
              'flex items-center gap-3 rounded-md px-3 py-2 transition-colors',
              i === step ? 'bg-slate-950 text-white' : i < step ? 'bg-teal-50 text-teal-800' : 'text-slate-400'
            )}
          >
            <span className={clsx(
              'flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold',
              i === step ? 'bg-white text-slate-950' : i < step ? 'bg-teal-600 text-white' : 'bg-slate-100 text-slate-500'
            )}>
              {i < step ? <Check size={14} /> : i + 1}
            </span>
            <span className="text-sm font-semibold">{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function StepHeading({ title, subtitle }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
      <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
    </div>
  )
}

function ReviewItem({ label, value }) {
  return (
    <div className="surface-muted p-4">
      <p className="text-xs font-semibold uppercase text-slate-400">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}
