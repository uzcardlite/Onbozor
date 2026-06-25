import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
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
  pending: { label: 'Kutilmoqda', cls: 'bg-tg-yellow/20 text-tg-yellow' },
  active: { label: 'Faol', cls: 'bg-tg-green/20 text-tg-green' },
  rejected: { label: 'Rad etildi', cls: 'bg-tg-red/20 text-tg-red' },
  deleted: { label: "O'chirildi", cls: 'bg-tg-muted/20 text-tg-muted' },
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
    enabled: !isDemo,
    retry: false,
  })

  const { data: shops } = useQuery({
    queryKey: ['my-shops'],
    queryFn: () => shopsAPI.my().then((r) => r.data),
    enabled: !isDemo,
    retry: false,
  })

  const changeRegion = (viloyat) => {
    haptic('selection')
    setRegion(viloyat)
    setUser({ ...user, viloyat })
    setRegionOpen(false)
    toast.success(`Viloyat: ${viloyat}`)
  }

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <div className="w-16 h-16 rounded-full bg-tg-accent/20 flex items-center justify-center text-2xl font-bold text-tg-accent shrink-0 overflow-hidden">
          {user?.avatar_url ? (
            <img src={user.avatar_url} alt="" className="w-full h-full object-cover" />
          ) : (
            user?.full_name?.charAt(0) || '?'
          )}
        </div>
        <div>
          <h1 className="text-lg font-bold">{user?.full_name || 'Foydalanuvchi'}</h1>
          {user?.username && <p className="text-xs text-tg-muted">@{user.username}</p>}
          {isDemo && <p className="text-[10px] text-tg-yellow mt-0.5">Demo rejim</p>}
        </div>
      </div>

      {isDemo && (
        <div className="bg-tg-yellow/10 border border-tg-yellow/20 rounded-xl p-3 mb-4">
          <p className="text-xs text-tg-yellow">
            Telegram orqali kiring — barcha imkoniyatlar ochiladi
          </p>
        </div>
      )}

      <div className="bg-tg-card rounded-2xl p-4 mb-4">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-xs text-tg-muted">Viloyat</p>
            <p className="text-sm font-medium mt-0.5">📍 {user?.viloyat || 'Tanlanmagan'}</p>
          </div>
          <button
            onClick={() => { haptic('impact'); setRegionOpen(!regionOpen) }}
            className="text-xs text-tg-accent"
          >
            O'zgartirish
          </button>
        </div>

        {regionOpen && (
          <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-white/5">
            {REGIONS.map((r) => (
              <button
                key={r}
                onClick={() => changeRegion(r)}
                className={`py-2 rounded-lg text-xs font-medium transition ${user?.viloyat === r ? 'bg-tg-accent text-white' : 'bg-tg-bg text-tg-muted'}`}
              >
                {r}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3 mb-6">
        <Link to="/referral" className="bg-tg-card rounded-2xl p-4 text-center transition active:scale-[0.98]">
          <p className="text-lg">👥</p>
          <p className="text-xs text-tg-muted mt-1">Referral</p>
        </Link>
        <Link to="/favourites" className="bg-tg-card rounded-2xl p-4 text-center transition active:scale-[0.98]">
          <p className="text-lg">❤️</p>
          <p className="text-xs text-tg-muted mt-1">Sevimlilar</p>
        </Link>
        <Link
          to={shops?.length ? `/shop/${shops[0].id}` : '/open-shop'}
          className="bg-tg-card rounded-2xl p-4 text-center transition active:scale-[0.98]"
        >
          <p className="text-lg">🏪</p>
          <p className="text-xs text-tg-muted mt-1">{shops?.length ? "Do'konim" : "Do'kon ochish"}</p>
        </Link>
      </div>

      <div>
        <div className="flex justify-between items-center mb-3">
          <h2 className="text-base font-semibold">Mening e'lonlarim</h2>
          <Link to="/add-listing" className="text-xs text-tg-accent">+ Yangi</Link>
        </div>

        {isDemo ? (
          <div className="text-center py-8">
            <p className="text-3xl mb-3">📢</p>
            <p className="text-sm text-tg-muted mb-2">Telegram orqali kiring</p>
            <Link to="/add-listing" className="text-sm text-tg-accent">E'lon berish →</Link>
          </div>
        ) : loadingListings ? (
          <div className="space-y-3 animate-pulse">
            {Array.from({ length: 3 }, (_, i) => <div key={i} className="bg-tg-card rounded-xl h-16" />)}
          </div>
        ) : listings?.length ? (
          <div className="space-y-2">
            {listings.map((l) => {
              const badge = STATUS_BADGE[l.status] || STATUS_BADGE.pending
              return (
                <Link key={l.id} to={`/listing/${l.id}`} className="bg-tg-card rounded-xl p-3 flex items-center gap-3 transition active:scale-[0.98] block">
                  <div className="w-12 h-12 rounded-lg bg-tg-bg overflow-hidden shrink-0">
                    {l.image_urls?.[0] ? (
                      <img src={l.image_urls[0]} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-tg-muted text-lg">📷</div>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{l.category}</p>
                    <p className="text-xs text-tg-accent">{formatPrice(l.price)} so'm</p>
                  </div>
                  <span className={`text-[10px] font-medium px-2 py-1 rounded-full ${badge.cls}`}>{badge.label}</span>
                </Link>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-sm text-tg-muted">Hali e'lonlar yo'q</p>
            <Link to="/add-listing" className="text-sm text-tg-accent mt-2 inline-block">E'lon berish →</Link>
          </div>
        )}
      </div>
    </div>
  )
}
