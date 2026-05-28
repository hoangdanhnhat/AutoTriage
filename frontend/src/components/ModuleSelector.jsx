const MODULE_GROUPS = [
  {
    title: 'Windows Modules',
    modules: [
      {
        key: 'collect_volatile_data',
        label: 'Volatile Data',
        desc: 'Processes, network connections, and system state',
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
        desc: 'AppCompat, scheduled tasks, services, and similar artifacts',
        default: true,
      },
      {
        key: 'collect_user_artifacts',
        label: 'User Artifacts',
        desc: 'Browser history, recent files, shell and PowerShell history',
        default: true,
      },
      {
        key: 'collect_program_data',
        label: 'ProgramData',
        desc: 'Startup items, WER, Defender, and application logs',
        default: true,
      },
      {
        key: 'collect_ntfs',
        label: 'NTFS Artifacts',
        desc: 'MFT dump for each fixed drive using RawCopy.exe',
        default: false,
      },
      {
        key: 'collect_prefetch',
        label: 'Prefetch Files',
        desc: 'Windows Prefetch .pf files',
        default: false,
      },
      {
        key: 'collect_memory',
        label: 'Memory Dump',
        desc: 'Full RAM dump with a supported memory tool',
        default: false,
      },
    ],
  },
  {
    title: 'Linux Modules',
    modules: [
      {
        key: 'collect_linux_volatile_data',
        label: 'Volatile Data',
        desc: 'Processes, network connections, and system state',
        default: true,
      },
      {
        key: 'collect_system_artifacts',
        label: 'System Artifacts',
        desc: 'OS release, users, services, cron, mounts, and packages',
        default: true,
      },
      {
        key: 'collect_log_artifacts',
        label: 'Log Artifacts',
        desc: 'System and application logs from common log paths',
        default: true,
      },
      {
        key: 'collect_linux_user_artifacts',
        label: 'User Artifacts',
        desc: 'Shell history, SSH files, and desktop user traces',
        default: true,
      },
      {
        key: 'collect_filesystem_artifacts',
        label: 'Filesystem Artifacts',
        desc: 'SUID files, world-writable paths, temp files, and recent files',
        default: true,
      },
      {
        key: 'collect_linux_memory',
        label: 'Memory Dump',
        desc: 'Memory acquisition with AVML or LiME when available',
        default: false,
      },
    ],
  },
]

export const MODULE_LABELS = Object.fromEntries(
  MODULE_GROUPS.flatMap((group) => group.modules.map((module) => [module.key, module.label]))
)

const MODULES = MODULE_GROUPS.flatMap((group) => group.modules)

export default function ModuleSelector({ value, onChange }) {
  function toggle(key) {
    onChange({ ...value, [key]: !value[key] })
  }

  return (
    <div className="space-y-5">
      {MODULE_GROUPS.map((group) => (
        <section key={group.title} className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-700">{group.title}</h3>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {group.modules.map((m) => (
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
        </section>
      ))}
    </div>
  )
}

export const DEFAULT_MODULES = Object.fromEntries(MODULES.map((m) => [m.key, false]))
