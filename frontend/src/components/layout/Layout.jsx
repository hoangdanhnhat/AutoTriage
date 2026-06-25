import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-transparent">
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-auto px-5 py-6 sm:px-8 lg:px-10">
        <Outlet />
      </main>
    </div>
  )
}
