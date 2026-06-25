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
    <div className="space-y-6">
      {MODULE_GROUPS.map((group) => (
        <section key={group.title} className="space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h3 className="section-title">{group.title}</h3>
            <span className="text-xs font-medium text-slate-400">
              {group.modules.filter((m) => value[m.key]).length} selected
            </span>
          </div>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            {group.modules.map((m) => (
              <label
                key={m.key}
                className="group flex min-h-[104px] cursor-pointer items-start gap-3 rounded-lg border border-slate-200 bg-white/80 p-4 transition-all duration-200 hover:-translate-y-0.5 hover:border-teal-300 hover:shadow-sm hover:shadow-slate-200/80 has-[:checked]:border-teal-400 has-[:checked]:bg-teal-50/70 has-[:checked]:ring-4 has-[:checked]:ring-teal-100"
              >
                <input
                  type="checkbox"
                  className="peer sr-only"
                  checked={!!value[m.key]}
                  onChange={() => toggle(m.key)}
                />
                <span className="mt-0.5 h-5 w-9 shrink-0 rounded-full bg-slate-200 p-0.5 transition-colors after:block after:h-4 after:w-4 after:rounded-full after:bg-white after:shadow-sm after:transition-transform peer-checked:bg-teal-600 peer-checked:after:translate-x-4" />
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-900">{m.label}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">{m.desc}</p>
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
