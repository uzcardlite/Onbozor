import { NavLink } from 'react-router-dom'
import { useTelegram } from '../hooks/useTelegram'
import { useUserStore } from '../store/useStore'

export default function BottomNav() {
  const { haptic } = useTelegram()
  const { user } = useUserStore()

  const tabs = [
    { to: '/', icon: '🏠', label: 'Bosh sahifa' },
    { to: '/search', icon: '🔍', label: 'Qidiruv' },
    { to: '/add-listing', icon: '➕', label: "E'lon" },
    ...(user?.is_admin ? [{ to: '/admin', icon: '🔧', label: 'Admin' }] : [{ to: '/favourites', icon: '❤️', label: 'Sevimli' }]),
    { to: '/profile', icon: '👤', label: 'Profil' },
  ]

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-tg-header border-t border-white/5 z-50 max-w-app mx-auto">
      <div className="flex justify-around items-center h-14">
        {tabs.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            onClick={() => haptic('selection')}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 text-xs transition-colors ${isActive ? 'text-tg-accent' : 'text-tg-muted'}`
            }
          >
            <span className="text-lg">{t.icon}</span>
            <span>{t.label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
