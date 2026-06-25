import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { ListSkeleton, ShopSkeleton } from '../components/LoadingSkeleton'
import { favouritesAPI } from '../api/endpoints'
import { useUserStore } from '../store/useStore'
import { useTelegram } from '../hooks/useTelegram'

function formatPrice(n) {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

export default function Favourites() {
  const [tab, setTab] = useState('shops')
  const { haptic } = useTelegram()
  const { token } = useUserStore()
  const qc = useQueryClient()
  const isDemo = !token || token === 'demo-token'

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['favourites'],
    queryFn: () => favouritesAPI.list().then((r) => r.data),
    enabled: !isDemo,
    retry: false,
  })

  const removeShopMut = useMutation({
    mutationFn: (id) => favouritesAPI.toggleShop(id),
    onSuccess: () => {
      haptic('notification', 'success')
      toast.success("Olib tashlandi")
      qc.invalidateQueries({ queryKey: ['favourites'] })
    },
    onError: () => toast.error("Xatolik yuz berdi"),
  })

  const removeListingMut = useMutation({
    mutationFn: (id) => favouritesAPI.toggleListing(id),
    onSuccess: () => {
      haptic('notification', 'success')
      toast.success("Olib tashlandi")
      qc.invalidateQueries({ queryKey: ['favourites'] })
    },
    onError: () => toast.error("Xatolik yuz berdi"),
  })

  const shops = data?.shops || []
  const listings = data?.listings || []

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <h1 className="text-xl font-bold mb-4">❤️ Sevimlilar</h1>

      <div className="flex gap-2 mb-4">
        {[
          ['shops', `🏪 Do'konlar (${shops.length})`],
          ['listings', `📢 E'lonlar (${listings.length})`],
        ].map(([key, label]) => (
          <button
            key={key}
            onClick={() => { haptic('selection'); setTab(key) }}
            className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition ${tab === key ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {isDemo ? (
        <div className="text-center py-16">
          <p className="text-3xl mb-3">❤️</p>
          <p className="text-sm text-tg-muted mb-2">Telegram orqali kiring</p>
          <p className="text-xs text-tg-muted">Sevimlilarni saqlash uchun tizimga kiring</p>
        </div>
      ) : isLoading ? (
        tab === 'shops' ? (
          <div className="space-y-3">{Array.from({ length: 3 }, (_, i) => <ShopSkeleton key={i} />)}</div>
        ) : <ListSkeleton count={4} />
      ) : isError ? (
        <div className="text-center py-16">
          <p className="text-3xl mb-3">⚠️</p>
          <p className="text-sm text-tg-muted mb-4">Ma'lumot olishda xatolik</p>
          <button onClick={() => refetch()} className="text-xs text-tg-accent">Qayta yuklash</button>
        </div>
      ) : tab === 'shops' ? (
        shops.length ? (
          <div className="space-y-3">
            {shops.map((s) => (
              <div key={s.id} className="bg-tg-card rounded-xl overflow-hidden">
                <Link to={`/shop/${s.id}`} className="flex items-center gap-3 p-3 transition active:scale-[0.98]">
                  <div className="w-12 h-12 rounded-xl bg-tg-bg flex items-center justify-center text-2xl shrink-0 overflow-hidden">
                    {s.icon_url ? <img src={s.icon_url} alt="" className="w-full h-full object-cover" /> : '🏪'}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <p className="text-sm font-semibold text-white truncate">{s.name}</p>
                      {s.is_verified && <span className="text-tg-accent text-xs">✓</span>}
                    </div>
                    <p className="text-xs text-tg-muted mt-0.5 truncate">{s.description}</p>
                    <p className="text-[11px] text-tg-muted mt-0.5">📍 {s.viloyat || 'Barcha viloyatlar'}</p>
                  </div>
                </Link>
                <div className="border-t border-white/5 px-3 py-2">
                  <button
                    onClick={() => { haptic('impact'); removeShopMut.mutate(s.id) }}
                    disabled={removeShopMut.isPending}
                    className="text-xs text-tg-red w-full text-center py-1 transition active:scale-95"
                  >
                    💔 Olib tashlash
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon="🏪" text="Sevimli do'konlar yo'q" sub="Do'konlar sahifasidan qo'shing" link="/shops" linkText="Do'konlarga o'tish →" />
        )
      ) : listings.length ? (
        <div className="space-y-3">
          {listings.map((l) => (
            <div key={l.id} className="bg-tg-card rounded-xl overflow-hidden">
              <Link to={`/listing/${l.id}`} className="flex items-center gap-3 p-3 transition active:scale-[0.98]">
                <div className="w-14 h-14 rounded-lg bg-tg-bg overflow-hidden shrink-0">
                  {l.image_urls?.[0] ? (
                    <img src={l.image_urls[0]} alt="" className="w-full h-full object-cover" loading="lazy" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-tg-muted text-lg">📷</div>
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">{l.category}</p>
                  <p className="text-sm font-bold text-tg-accent">{formatPrice(l.price)} so'm</p>
                  <p className="text-[11px] text-tg-muted">📍 {l.viloyat}</p>
                </div>
                {l.is_promoted && (
                  <span className="text-[9px] font-bold bg-tg-yellow text-black px-1.5 py-0.5 rounded-full shrink-0">TOP</span>
                )}
              </Link>
              <div className="border-t border-white/5 px-3 py-2">
                <button
                  onClick={() => { haptic('impact'); removeListingMut.mutate(l.id) }}
                  disabled={removeListingMut.isPending}
                  className="text-xs text-tg-red w-full text-center py-1 transition active:scale-95"
                >
                  💔 Olib tashlash
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon="📢" text="Saqlangan e'lonlar yo'q" sub="E'lonlarni ♥ bosib saqlang" link="/" linkText="E'lonlarga o'tish →" />
      )}
    </div>
  )
}

function EmptyState({ icon, text, sub, link, linkText }) {
  return (
    <div className="text-center py-16">
      <p className="text-3xl mb-3">{icon}</p>
      <p className="text-sm text-tg-muted mb-1">{text}</p>
      <p className="text-xs text-tg-muted mb-4">{sub}</p>
      <Link to={link} className="text-xs text-tg-accent">{linkText}</Link>
    </div>
  )
}
