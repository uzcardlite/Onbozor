import { NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useTelegram } from '../hooks/useTelegram'
import { useUserStore } from '../store/useStore'
import { messagesAPI } from '../api/endpoints'

export default function BottomNav() {
  const { haptic } = useTelegram()
  const { user, token } = useUserStore()
  const isDemo = !token || token === 'demo-token'

  const { data: unread } = useQuery({
    queryKey: ['unread-messages'],
    queryFn: () => messagesAPI.unreadCount().then((r) => r.data.count),
    enabled: !isDemo,
    refetchInterval: 15000,
    retry: false,
  })

  const tabs = [
    { to: '/', icon: '🏠', label: 'Bosh sahifa' },
    { to: '/search', icon: '🔍', label: 'Qidiruv' },
    { to: '/add-listing', icon: '➕', label: "E'lon", isCenter: true },
    { to: '/messages', icon: '💬', label: 'Xabarlar', badge: unread || 0 },
    ...(localStorage.getItem('admin_authenticated') === 'true' ? [{ to: '/admin', icon: '🔧', label: 'Admin' }] : [{ to: '/profile', icon: '👤', label: 'Profil' }]),
  ]

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 max-w-app mx-auto">
      <div className="bg-tg-header/95 backdrop-blur-lg border-t border-tg-border/40">
        <div className="flex justify-around items-end h-16 px-1 pb-1">
          {tabs.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              onClick={() => haptic('selection')}
              className={({ isActive }) =>
                t.isCenter
                  ? 'flex flex-col items-center -mt-4'
                  : `flex flex-col items-center gap-0.5 py-1.5 px-2 rounded-lg transition-colors duration-150 relative ${isActive ? 'text-tg-accent' : 'text-tg-muted'}`
              }
            >
              {t.isCenter ? (
                <div className="w-12 h-12 rounded-full bg-tg-accent flex items-center justify-center text-white text-xl shadow-lg shadow-tg-accent/30 active:scale-95 transition-transform">
                  {t.icon}
                </div>
              ) : (
                <>
                  <span className="text-lg leading-none relative">
                    {t.icon}
                    {t.badge > 0 && (
                      <span className="absolute -top-1 -right-2.5 min-w-[14px] h-[14px] bg-tg-red rounded-full text-[8px] font-bold flex items-center justify-center text-white px-0.5">
                        {t.badge > 9 ? '9+' : t.badge}
                      </span>
                    )}
                  </span>
                  <span className="text-[10px] leading-none">{t.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}
