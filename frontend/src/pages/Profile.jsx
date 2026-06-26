import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { listingsAPI, shopsAPI, analyticsAPI, gamificationAPI, paymentsAPI } from '../api/endpoints'
import { useUserStore, useAppStore } from '../store/useStore'
import { useTelegram } from '../hooks/useTelegram'

const REGIONS = [
  "Toshkent", "Samarqand", "Buxoro", "Andijon", "Farg'ona",
  "Namangan", "Qashqadaryo", "Surxondaryo", "Sirdaryo",
  "Jizzax", "Navoiy", "Xorazm", "Qoraqalpog'iston",
]

const STATUS_BADGE = {
  pending: { label: 'Kutilmoqda', cls: 'bg-tg-yellow/15 text-tg-yellow' },
  active: { label: 'Faol', cls: 'bg-tg-green/15 text-tg-green' },
  rejected: { label: 'Rad etildi', cls: 'bg-tg-red/15 text-tg-red' },
  deleted: { label: "O'chirildi", cls: 'bg-tg-muted/15 text-tg-muted' },
}

function formatPrice(n) {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

export default function Profile() {
  const { user, setUser, token } = useUserStore()
  const { setRegion } = useAppStore()
  const { haptic } = useTelegram()
  const [regionOpen, setRegionOpen] = useState(false)
  const isDemo = !token || token === 'demo-token'

  const { data: listings, isLoading: loadingListings } = useQuery({
    queryKey: ['my-listings'],
    queryFn: () => listingsAPI.my().then((r) => r.data),
    enabled: !isDemo, retry: false,
  })

  const { data: shops } = useQuery({
    queryKey: ['my-shops'],
    queryFn: () => shopsAPI.my().then((r) => r.data),
    enabled: !isDemo, retry: false,
  })

  const { data: payments } = useQuery({
    queryKey: ['my-payments'],
    queryFn: () => paymentsAPI.my().then((r) => r.data),
    enabled: !isDemo, retry: false,
  })

  const { data: analytics } = useQuery({
    queryKey: ['my-analytics'],
    queryFn: () => analyticsAPI.my().then((r) => r.data),
    enabled: !isDemo, retry: false,
  })

  const { data: gameStats } = useQuery({
    queryKey: ['my-game-stats'],
    queryFn: () => gamificationAPI.myStats().then((r) => r.data),
    enabled: !isDemo, retry: false,
  })

  const LEVEL_NAMES = { 1: 'Yangi', 2: 'Faol', 3: 'Tajribali', 4: 'Professional', 5: 'Ekspert ⭐' }

  const changeRegion = (viloyat) => {
    haptic('selection')
    setRegion(viloyat)
    setUser({ ...user, viloyat })
    setRegionOpen(false)
    toast.success(`📍 ${viloyat}`)
  }

  const initial = user?.full_name?.charAt(0)?.toUpperCase() || '?'

  return (
    <div className="pb-20 max-w-app mx-auto">
      <div className="bg-gradient-to-br from-tg-accent/20 via-tg-header to-tg-bg px-4 pt-6 pb-8 rounded-b-3xl">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-tg-accent to-blue-600 flex items-center justify-center text-2xl font-bold text-white shrink-0 shadow-lg shadow-tg-accent/20">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="" className="w-full h-full object-cover rounded-full" />
            ) : initial}
          </div>
          <div>
            <h1 className="text-lg font-bold">{user?.full_name || 'Foydalanuvchi'}</h1>
            {user?.username && <p className="text-xs text-tg-muted">@{user.username}</p>}
            {isDemo && <span className="text-[9px] bg-tg-yellow/15 text-tg-yellow px-2 py-0.5 rounded mt-1 inline-block">Demo</span>}
          </div>
        </div>
      </div>

      <div className="px-4 -mt-4">
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="card p-3 text-center">
            <p className="text-lg font-bold text-tg-accent animate-count-up">{analytics?.total_views || 0}</p>
            <p className="text-[10px] text-tg-muted mt-0.5">Ko'rishlar</p>
          </div>
          <div className="card p-3 text-center">
            <p className="text-lg font-bold text-tg-green animate-count-up">{analytics?.total_listings || listings?.length || 0}</p>
            <p className="text-[10px] text-tg-muted mt-0.5">E'lonlar</p>
          </div>
          <div className="card p-3 text-center">
            <p className="text-lg font-bold text-purple-400 animate-count-up">{analytics?.total_favourites || 0}</p>
            <p className="text-[10px] text-tg-muted mt-0.5">Sevimlilar</p>
          </div>
        </div>

        <div className="card p-4 mb-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-[10px] text-tg-muted uppercase tracking-wider">Viloyat</p>
              <p className="text-sm font-medium mt-0.5">📍 {user?.viloyat || 'Tanlanmagan'}</p>
            </div>
            <button onClick={() => { haptic('impact'); setRegionOpen(!regionOpen) }} className="text-xs text-tg-accent font-medium">
              {regionOpen ? 'Yopish' : "O'zgartirish"}
            </button>
          </div>
          {regionOpen && (
            <div className="grid grid-cols-2 gap-1.5 mt-3 pt-3 border-t border-tg-border animate-fade-in">
              {REGIONS.map((r) => (
                <button key={r} onClick={() => changeRegion(r)}
                  className={`py-2 rounded-lg text-xs font-medium transition-all ${user?.viloyat === r ? 'bg-tg-accent text-white' : 'bg-tg-bg text-tg-muted hover:text-white'}`}>
                  {r}
                </button>
              ))}
            </div>
          )}
        </div>

        {!isDemo && gameStats && (
          <div className="card p-4 mb-4">
            <div className="flex justify-between items-center mb-2">
              <div>
                <span className="text-xs text-tg-muted">Daraja: </span>
                <span className="text-xs font-bold">{LEVEL_NAMES[gameStats.level]}</span>
              </div>
              <Link to="/leaderboard" className="text-[10px] text-tg-accent">🏆 Reyting →</Link>
            </div>
            <div className="flex items-center gap-2 mb-2">
              <div className="flex-1 h-2 bg-tg-bg rounded-full overflow-hidden">
                <div className="h-full bg-tg-accent rounded-full transition-all duration-500" style={{ width: `${gameStats.progress}%` }} />
              </div>
              <span className="text-[10px] text-tg-muted">{gameStats.points}/{gameStats.next_level}</span>
            </div>
            {gameStats.badges?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {gameStats.badges.map((b) => (
                  <span key={b.type} className={`text-[10px] px-2 py-0.5 rounded-md ${b.earned ? 'bg-tg-yellow/15 text-tg-yellow' : 'bg-tg-bg text-tg-muted/40'}`} title={b.desc}>
                    {b.emoji} {b.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-2 gap-2 mb-6">
          <Link to="/referral" className="card p-3.5 flex items-center gap-2.5 active:scale-[0.98] transition-transform">
            <span className="text-xl">👥</span>
            <span className="text-xs font-medium">Referral</span>
          </Link>
          <Link to="/favourites" className="card p-3.5 flex items-center gap-2.5 active:scale-[0.98] transition-transform">
            <span className="text-xl">❤️</span>
            <span className="text-xs font-medium">Sevimlilar</span>
          </Link>
        </div>

        {!isDemo && analytics?.views_by_day?.length > 0 && (
          <div className="card p-4 mb-4">
            <h3 className="text-xs font-semibold mb-3">📊 Oxirgi 7 kun ko'rishlari</h3>
            <div className="flex items-end gap-1 h-20">
              {analytics.views_by_day.map((d) => {
                const max = Math.max(...analytics.views_by_day.map((x) => x.views), 1)
                const h = Math.max((d.views / max) * 100, 4)
                return (
                  <div key={d.date} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-[8px] text-tg-muted">{d.views}</span>
                    <div className="w-full bg-tg-accent/80 rounded-t" style={{ height: `${h}%` }} />
                    <span className="text-[7px] text-tg-muted">{d.date.slice(5)}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {!isDemo && analytics?.top_listings?.length > 0 && (
          <div className="card p-4 mb-4">
            <h3 className="text-xs font-semibold mb-3">🏆 Eng ko'p ko'rilgan</h3>
            <div className="space-y-2">
              {analytics.top_listings.map((l, i) => (
                <Link key={l.id} to={`/listing/${l.id}`} className="flex items-center gap-2 text-xs">
                  <span className="text-tg-yellow font-bold w-4">{i + 1}.</span>
                  <span className="flex-1 truncate">{l.category}</span>
                  <span className="text-tg-muted">👁 {l.views}</span>
                </Link>
              ))}
            </div>
          </div>
        )}

        <div>
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-sm font-semibold">Mening e'lonlarim</h2>
            <Link to="/add-listing" className="text-xs text-tg-accent font-medium">+ Yangi</Link>
          </div>

          {isDemo ? (
            <div className="card text-center py-10">
              <p className="text-3xl mb-2">📢</p>
              <p className="text-sm text-tg-muted mb-1">Telegram orqali kiring</p>
              <Link to="/add-listing" className="text-xs text-tg-accent">E'lon berish →</Link>
            </div>
          ) : loadingListings ? (
            <div className="space-y-2">{Array.from({ length: 3 }, (_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}</div>
          ) : listings?.length ? (
            <div className="space-y-2">
              {listings.map((l) => {
                const badge = STATUS_BADGE[l.status] || STATUS_BADGE.pending
                return (
                  <Link key={l.id} to={`/listing/${l.id}`} className="card p-3 flex items-center gap-3 active:scale-[0.98] transition-transform block">
                    <div className="w-12 h-12 rounded-lg bg-tg-bg overflow-hidden shrink-0">
                      {l.image_urls?.[0] ? (
                        <img src={l.image_urls[0]} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-tg-muted text-lg">📷</div>
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">{l.category}</p>
                      <p className="text-xs text-tg-green font-bold">{formatPrice(l.price)} so'm</p>
                    </div>
                    <span className={`text-[9px] font-semibold px-2 py-1 rounded-md ${badge.cls}`}>{badge.label}</span>
                  </Link>
                )
              })}
            </div>
          ) : (
            <div className="card text-center py-10">
              <p className="text-sm text-tg-muted">Hali e'lonlar yo'q</p>
              <Link to="/add-listing" className="text-xs text-tg-accent mt-2 inline-block">E'lon berish →</Link>
            </div>
          )}
        </div>

        {!isDemo && payments?.length > 0 && (
          <div className="mt-6">
            <h2 className="text-sm font-semibold mb-3">💳 To'lovlar tarixi</h2>
            <div className="space-y-2">
              {payments.slice(0, 10).map((p) => {
                const statusMap = { paid: { label: "To'landi", cls: 'text-tg-green' }, pending: { label: 'Kutilmoqda', cls: 'text-tg-yellow' }, failed: { label: 'Xato', cls: 'text-tg-red' }, cancelled: { label: 'Bekor', cls: 'text-tg-muted' } }
                const s = statusMap[p.status] || statusMap.pending
                return (
                  <div key={p.id} className="card p-3 flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-tg-bg flex items-center justify-center text-lg shrink-0">
                      {p.type === 'shop' ? '🏪' : p.type === 'promotion' ? '🚀' : '💳'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate">{p.shop_name || 'Promosiya'}</p>
                      <p className="text-[10px] text-tg-muted">{new Date(p.created_at).toLocaleDateString('uz')} · {p.method}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-xs font-bold">{formatPrice(p.amount)} so'm</p>
                      <p className={`text-[10px] font-medium ${s.cls}`}>{s.label}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
