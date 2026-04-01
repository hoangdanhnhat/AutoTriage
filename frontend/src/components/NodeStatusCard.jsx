import clsx from 'clsx'

const statusConfig = {
  online:  { dot: 'bg-green-500',  label: 'Online',  badge: 'bg-green-100 text-green-800' },
  offline: { dot: 'bg-red-500',    label: 'Offline', badge: 'bg-red-100 text-red-800' },
  unknown: { dot: 'bg-gray-400',   label: 'Unknown', badge: 'bg-gray-100 text-gray-600' },
}

export default function NodeStatusCard({ node, selected, onToggle }) {
  const cfg = statusConfig[node.status] ?? statusConfig.unknown
  return (
    <div
      onClick={() => onToggle?.(node)}
      className={clsx(
        'border rounded-lg p-4 cursor-pointer transition-all',
        selected
          ? 'border-cyan-500 ring-2 ring-cyan-300 bg-cyan-50'
          : 'border-gray-200 bg-white hover:border-gray-300'
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-sm font-semibold text-gray-800">{node.ip_address}</span>
        <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', cfg.badge)}>
          <span className={clsx('inline-block w-2 h-2 rounded-full mr-1', cfg.dot)} />
          {cfg.label}
        </span>
      </div>
      {node.hostname && (
        <p className="text-xs text-gray-500 truncate">{node.hostname}</p>
      )}
      <p className="text-xs text-gray-400 mt-1">{node.group_name ?? 'ungrouped'}</p>
      {node.last_checked && (
        <p className="text-xs text-gray-300 mt-1">
          Checked {new Date(node.last_checked).toLocaleTimeString()}
        </p>
      )}
    </div>
  )
}
