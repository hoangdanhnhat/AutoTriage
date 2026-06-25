import clsx from 'clsx'
import { Check, Monitor } from 'lucide-react'

const statusConfig = {
  online:  { dot: 'bg-emerald-500', label: 'Online',  badge: 'bg-emerald-50 text-emerald-700 ring-emerald-200' },
  offline: { dot: 'bg-rose-500',    label: 'Offline', badge: 'bg-rose-50 text-rose-700 ring-rose-200' },
  unknown: { dot: 'bg-slate-400',   label: 'Unknown', badge: 'bg-slate-100 text-slate-600 ring-slate-200' },
}

export default function NodeStatusCard({ node, selected, onToggle }) {
  const cfg = statusConfig[node.status] ?? statusConfig.unknown
  return (
    <div
      onClick={() => onToggle?.(node)}
      className={clsx(
        'group relative min-h-[132px] cursor-pointer rounded-lg border p-4 transition-all duration-200',
        selected
          ? 'border-teal-400 bg-teal-50/80 shadow-sm shadow-teal-900/10 ring-4 ring-teal-100'
          : 'border-slate-200 bg-white/90 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md hover:shadow-slate-200/80'
      )}
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-slate-100 text-slate-600 transition-colors group-hover:bg-slate-200">
          <Monitor size={17} />
        </div>
        <span className={clsx('status-pill ring-1', cfg.badge)}>
          <span className={clsx('h-2 w-2 rounded-full', cfg.dot)} />
          {cfg.label}
        </span>
      </div>
      <span className="mono-value block font-semibold">{node.ip_address}</span>
      {node.hostname && (
        <p className="mt-1 truncate text-sm text-slate-600">{node.hostname}</p>
      )}
      <p className="mt-2 text-xs font-medium uppercase text-slate-400">{node.group_name ?? 'ungrouped'}</p>
      {node.last_checked && (
        <p className="mt-1 text-xs text-slate-400">
          Checked {new Date(node.last_checked).toLocaleTimeString()}
        </p>
      )}
      {selected && (
        <div className="absolute bottom-3 right-3 flex h-6 w-6 items-center justify-center rounded-full bg-teal-600 text-white">
          <Check size={14} />
        </div>
      )}
    </div>
  )
}
