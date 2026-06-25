import { useState } from 'react'
import clsx from 'clsx'
import { ChevronDown, ChevronRight } from 'lucide-react'

const nodeStatusConfig = {
  pending:   { badge: 'bg-slate-100 text-slate-600 ring-slate-200', label: 'Pending' },
  running:   { badge: 'bg-blue-50 text-blue-700 ring-blue-200', label: 'Running' },
  completed: { badge: 'bg-emerald-50 text-emerald-700 ring-emerald-200', label: 'Completed' },
  failed:    { badge: 'bg-rose-50 text-rose-700 ring-rose-200', label: 'Failed' },
  skipped:   { badge: 'bg-amber-50 text-amber-700 ring-amber-200', label: 'Skipped' },
}

function NodeRow({ ns }) {
  const [expanded, setExpanded] = useState(false)
  const cfg = nodeStatusConfig[ns.status] ?? nodeStatusConfig.pending

  const duration =
    ns.started_at && ns.completed_at
      ? Math.round(
          (new Date(ns.completed_at) - new Date(ns.started_at)) / 1000
        ) + 's'
      : ns.started_at
      ? 'running...'
      : '-'

  return (
    <>
      <tr className="table-row">
        <td className="px-4 py-3">
          <span className="mono-value">{ns.ip_address}</span>
        </td>
        <td className="px-4 py-3 text-sm text-slate-600">{ns.hostname ?? '-'}</td>
        <td className="px-4 py-3">
          <span className={clsx('status-pill ring-1', cfg.badge)}>
            {ns.status === 'running' && <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-soft-pulse" />}
            {cfg.label}
          </span>
        </td>
        <td className="px-4 py-3 text-sm text-slate-500">{duration}</td>
        <td className="px-4 py-3">
          {ns.artifact_path && (
            <span className="status-pill bg-teal-50 text-teal-700 ring-1 ring-teal-200">ZIP ready</span>
          )}
        </td>
        <td className="px-4 py-3">
          {ns.output_log && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="muted-link text-xs text-slate-500"
            >
              {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              Log
            </button>
          )}
        </td>
      </tr>
      {expanded && ns.output_log && (
        <tr>
          <td colSpan={6} className="px-4 pb-4">
            <pre className="max-h-56 overflow-auto rounded-lg bg-slate-950 p-4 text-xs leading-5 text-emerald-300 shadow-inner shadow-black/30 whitespace-pre-wrap">
              {ns.output_log}
            </pre>
          </td>
        </tr>
      )}
    </>
  )
}

export default function TriageProgressTable({ nodeStatuses, liveData }) {
  const merged = nodeStatuses.map((ns) => {
    const live = liveData?.[ns.ip_address]
    if (!live) return ns
    return { ...ns, status: live.status ?? ns.status }
  })

  return (
    <div className="table-shell overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="table-head">
          <tr>
            <th className="px-4 py-3 text-left">IP Address</th>
            <th className="px-4 py-3 text-left">Hostname</th>
            <th className="px-4 py-3 text-left">Status</th>
            <th className="px-4 py-3 text-left">Duration</th>
            <th className="px-4 py-3 text-left">Artifact</th>
            <th className="px-4 py-3 text-left">Log</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {merged.map((ns) => (
            <NodeRow key={ns.id} ns={ns} />
          ))}
          {merged.length === 0 && (
            <tr>
              <td colSpan={6} className="px-4 py-8 text-center text-sm text-slate-400">
                No nodes
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
