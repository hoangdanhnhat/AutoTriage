import { useState } from 'react'
import clsx from 'clsx'
import { ChevronDown, ChevronRight } from 'lucide-react'

const nodeStatusConfig = {
  pending:   { badge: 'bg-gray-100 text-gray-600',   label: 'Pending' },
  running:   { badge: 'bg-blue-100 text-blue-700',   label: 'Running' },
  completed: { badge: 'bg-green-100 text-green-700', label: 'Completed' },
  failed:    { badge: 'bg-red-100 text-red-700',     label: 'Failed' },
  skipped:   { badge: 'bg-yellow-100 text-yellow-700', label: 'Skipped' },
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
      ? 'running…'
      : '—'

  return (
    <>
      <tr className="hover:bg-gray-50 transition-colors">
        <td className="px-4 py-3 font-mono text-sm">{ns.ip_address}</td>
        <td className="px-4 py-3 text-sm text-gray-600">{ns.hostname ?? '—'}</td>
        <td className="px-4 py-3">
          <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', cfg.badge)}>
            {cfg.label}
          </span>
        </td>
        <td className="px-4 py-3 text-sm text-gray-500">{duration}</td>
        <td className="px-4 py-3">
          {ns.artifact_path && (
            <span className="text-xs text-cyan-600 font-medium">ZIP ready</span>
          )}
        </td>
        <td className="px-4 py-3">
          {ns.output_log && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800"
            >
              {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              Log
            </button>
          )}
        </td>
      </tr>
      {expanded && ns.output_log && (
        <tr>
          <td colSpan={6} className="px-4 pb-3">
            <pre className="bg-gray-900 text-green-400 text-xs p-3 rounded overflow-auto max-h-48 whitespace-pre-wrap">
              {ns.output_log}
            </pre>
          </td>
        </tr>
      )}
    </>
  )
}

export default function TriageProgressTable({ nodeStatuses, liveData }) {
  // Merge live updates into node statuses for display
  const merged = nodeStatuses.map((ns) => {
    const live = liveData?.[ns.ip_address]
    if (!live) return ns
    return { ...ns, status: live.status ?? ns.status }
  })

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-xs uppercase text-gray-500">
          <tr>
            <th className="px-4 py-3 text-left">IP Address</th>
            <th className="px-4 py-3 text-left">Hostname</th>
            <th className="px-4 py-3 text-left">Status</th>
            <th className="px-4 py-3 text-left">Duration</th>
            <th className="px-4 py-3 text-left">Artifact</th>
            <th className="px-4 py-3 text-left">Log</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {merged.map((ns) => (
            <NodeRow key={ns.id} ns={ns} />
          ))}
          {merged.length === 0 && (
            <tr>
              <td colSpan={6} className="px-4 py-6 text-center text-gray-400 text-sm">
                No nodes
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
