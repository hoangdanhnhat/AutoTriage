const MODULES = [
  {
    key: 'collect_volatile_data',
    label: 'Volatile Data',
    desc: 'Running processes, network connections',
    default: true,
  },
  {
    key: 'collect_registry',
    label: 'Registry Hives',
    desc: 'SAM, SECURITY, SOFTWARE, SYSTEM, user NTUSERs',
    default: true,
  },
  {
    key: 'collect_event_logs',
    label: 'Event Logs',
    desc: 'Windows .evtx log files',
    default: true,
  },
  {
    key: 'collect_windows_artifacts',
    label: 'Windows Artifacts',
    desc: 'Prefetch, AppCompat, scheduled tasks, etc.',
    default: true,
  },
  {
    key: 'collect_user_artifacts',
    label: 'User Artifacts',
    desc: 'Browser history, recent files, PowerShell history',
    default: true,
  },
  {
    key: 'collect_program_data',
    label: 'ProgramData',
    desc: 'Startup items, WER, Defender, 3rd-party app logs',
    default: true,
  },
  {
    key: 'collect_ntfs',
    label: 'NTFS Artifacts',
    desc: 'MFT dump for each fixed drive (requires RawCopy.exe)',
    default: false,
  },
  {
    key: 'collect_prefetch',
    label: 'Prefetch Files',
    desc: 'Windows Prefetch .pf files (separate pass)',
    default: false,
  },
  {
    key: 'collect_memory',
    label: 'Memory Dump',
    desc: 'Full RAM dump via DumpIt.exe (requires DumpIt in Tools/)',
    default: false,
  },
]

export default function ModuleSelector({ value, onChange }) {
  function toggle(key) {
    onChange({ ...value, [key]: !value[key] })
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {MODULES.map((m) => (
        <label
          key={m.key}
          className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 cursor-pointer hover:border-cyan-300 transition-colors"
        >
          <input
            type="checkbox"
            className="mt-0.5 accent-cyan-600"
            checked={!!value[m.key]}
            onChange={() => toggle(m.key)}
          />
          <div>
            <p className="text-sm font-medium text-gray-800">{m.label}</p>
            <p className="text-xs text-gray-500">{m.desc}</p>
          </div>
        </label>
      ))}
    </div>
  )
}

export const DEFAULT_MODULES = Object.fromEntries(MODULES.map((m) => [m.key, m.default]))
