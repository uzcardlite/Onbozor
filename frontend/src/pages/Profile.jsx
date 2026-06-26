import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { listingsAPI, shopsAPI } from '../api/endpoints'
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
          <Link to="/referral" onClick={() => haptic('impact', 'light')} className="card p-3 text-center active:scale-95 transition-transform">
            <p className="text-lg font-bold text-tg-accent animate-count-up">{user?.ref_count || 0}</p>
            <p className="text-[10px] text-tg-muted mt-0.5">Referrallar</p>
          </Link>
          <div className="card p-3 text-center">
            <p className="text-lg font-bold text-tg-green animate-count-up">{listings?.length || 0}</p>
            <p className="text-[10px] text-tg-muted mt-0.5">E'lonlar</p>
          </div>
          <Link
            to={shops?.length ? `/shop/${shops[0].id}` : '/open-shop'}
            onClick={() => haptic('impact', 'light')}
            className="card p-3 text-center active:scale-95 transition-transform"
          >
            <p className="text-lg font-bold text-purple-400 animate-count-up">{shops?.length || 0}</p>
            <p className="text-[10px] text-tg-muted mt-0.5">Do'konlar</p>
          </Link>
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
      </div>
    </div>
  )
}
