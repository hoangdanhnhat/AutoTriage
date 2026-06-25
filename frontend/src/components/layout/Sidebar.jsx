import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, FolderOpen, Scan, LogOut, ShieldCheck } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/inventories', label: 'Inventories', icon: FolderOpen },
  { to: '/triage', label: 'Triage Jobs', icon: Scan },
]

export default function Sidebar() {
  const logout = useAuthStore((s) => s.logout)
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-slate-900/10 bg-slate-950 text-slate-100 shadow-2xl shadow-slate-950/10">
      <div className="px-5 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-500/15 text-teal-300 ring-1 ring-teal-400/20">
            <ShieldCheck size={20} />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">Forensics IR</p>
            <p className="text-xs text-slate-400">Auto triage console</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'group flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-white text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:bg-white/10 hover:text-white'
              )
            }
          >
            <Icon size={18} className="shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="m-3 rounded-lg border border-white/10 bg-white/5 p-3 text-sm">
        <p className="truncate text-xs uppercase text-slate-500">Signed in</p>
        <p className="mt-1 truncate font-medium text-slate-200">{user?.username}</p>
        <button
          onClick={handleLogout}
          className="mt-3 flex w-full items-center gap-2 rounded-md px-2 py-2 text-slate-400 transition-colors hover:bg-rose-500/10 hover:text-rose-300"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
