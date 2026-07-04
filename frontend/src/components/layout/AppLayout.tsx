import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, FolderKanban, Settings, LogOut, Film,
  Users, ImageIcon, Package, Database, ChevronDown, ChevronRight,
} from 'lucide-react'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import { clsx } from 'clsx'

interface NavGroupDef {
  label: string
  items: { to: string; label: string; Icon: React.ElementType }[]
}

const NAV_GROUPS: NavGroupDef[] = [
  {
    label: 'Library',
    items: [
      { to: '/library/characters', label: 'Characters', Icon: Users },
      { to: '/library/backgrounds', label: 'Backgrounds', Icon: ImageIcon },
      { to: '/library/props', label: 'Props', Icon: Package },
    ],
  },
  {
    label: 'Studio',
    items: [
      { to: '/studio/asset-manager', label: 'Asset Manager', Icon: Database },
    ],
  },
]

function NavGroup({ group }: { group: NavGroupDef }) {
  const [open, setOpen] = useState(true)
  return (
    <div className="mt-1">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center w-full px-3 py-1 text-xs font-semibold uppercase tracking-wider text-gray-600 hover:text-gray-400 transition-colors"
      >
        <span className="flex-1 text-left">{group.label}</span>
        {open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
      </button>
      {open && (
        <div className="mt-0.5 ml-1 space-y-0.5">
          {group.items.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                  isActive
                    ? 'bg-brand-600/20 text-brand-400'
                    : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'
                )
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  )
}

export function AppLayout() {
  const { user, refreshToken, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    if (refreshToken) {
      try { await authApi.logout(refreshToken) } catch { /* ignore */ }
    }
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-950">
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col overflow-y-auto">
        {/* Logo */}
        <div className="p-4 border-b border-gray-800 flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
              <Film className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">AI Animation</p>
              <p className="text-xs text-gray-500">Studio Platform</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5">
          {/* Core */}
          {[
            { to: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
            { to: '/projects', label: 'Projects', Icon: FolderKanban },
          ].map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                  isActive
                    ? 'bg-brand-600/20 text-brand-400'
                    : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'
                )
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}

          <div className="pt-2 pb-1 border-t border-gray-800 mt-2" />

          {/* Module 2 groups */}
          {NAV_GROUPS.map((g) => <NavGroup key={g.label} group={g} />)}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-gray-800 flex-shrink-0">
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors mb-1',
                isActive
                  ? 'bg-brand-600/20 text-brand-400'
                  : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'
              )
            }
          >
            <Settings className="w-4 h-4" />
            Settings
          </NavLink>
          <div className="flex items-center gap-3 px-3 py-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-brand-700 flex items-center justify-center text-xs font-semibold text-white flex-shrink-0">
              {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-200 truncate">{user?.full_name || 'User'}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-400 hover:text-red-400 hover:bg-red-900/20 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
