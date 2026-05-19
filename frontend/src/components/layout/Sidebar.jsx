import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, FolderOpen, Scan, LogOut } from 'lucide-react'
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
    <aside className="flex flex-col w-56 min-h-screen bg-gray-900 text-gray-100">
      <div className="px-6 py-5 border-b border-gray-700">
        <span className="text-lg font-bold tracking-wide text-cyan-400">ForensicsIR</span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-cyan-700 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              )
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-gray-700 text-sm">
        <p className="text-gray-400 truncate">{user?.username}</p>
        <button
          onClick={handleLogout}
          className="mt-2 flex items-center gap-2 text-gray-400 hover:text-red-400 transition-colors"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
