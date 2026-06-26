import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import ProductCard from '../components/ProductCard'
import ShopCard from '../components/ShopCard'
import { ListSkeleton, ShopSkeleton } from '../components/LoadingSkeleton'
import { listingsAPI, shopsAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'
import { usePullRefresh } from '../hooks/usePullRefresh'

const CATEGORIES = [
  { slug: 'uyjoy', emoji: '🏠', label: 'Uy-joy', gradient: 'from-blue-600 to-cyan-500' },
  { slug: 'texnika', emoji: '📱', label: 'Texnika', gradient: 'from-violet-600 to-purple-500' },
  { slug: 'avto', emoji: '🚗', label: 'Avtomobil', gradient: 'from-orange-600 to-amber-500' },
  { slug: 'moto', emoji: '🏍', label: 'Moto', gradient: 'from-rose-600 to-pink-500' },
  { slug: 'kiyim', emoji: '👕', label: 'Kiyim', gradient: 'from-emerald-600 to-green-500' },
]

function PopularSection() {
  const viewed = (() => {
    try { return JSON.parse(localStorage.getItem('viewed_categories') || '[]') } catch { return [] }
  })()
  const topCategory = viewed.length > 0
    ? [...new Set(viewed)].sort((a, b) => viewed.filter((x) => x === b).length - viewed.filter((x) => x === a).length)[0]
    : null

  const { data, isLoading } = useQuery({
    queryKey: ['popular', topCategory],
    queryFn: () => listingsAPI.list({ sort: 'popular', limit: 4, category: topCategory }).then((r) => r.data),
  })

  if (isLoading || !data?.length) return null

  return (
    <div className="px-4 mt-6">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-base font-semibold">🔥 {topCategory ? `${topCategory} uchun` : 'Mashhur'}</h2>
        <Link to={`/search?sort=popular`} className="text-xs text-tg-accent font-medium">Barchasi →</Link>
      </div>
      <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 snap-x">
        {data.map((l) => (
          <div key={l.id} className="min-w-[160px] snap-start shrink-0">
            <ProductCard listing={l} />
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Home() {
  const { haptic } = useTelegram()

  const { data: listings, isLoading: loadingListings, refetch: refetchListings } = useQuery({
    queryKey: ['listings', 'home'],
    queryFn: () => listingsAPI.list({ limit: 10 }).then((r) => r.data),
    retry: 1,
  })

  const { data: shops, isLoading: loadingShops, refetch: refetchShops } = useQuery({
    queryKey: ['shops', 'home'],
    queryFn: () => shopsAPI.list({ limit: 10 }).then((r) => r.data),
    retry: 1,
  })

  const refreshing = usePullRefresh(async () => {
    await Promise.all([refetchListings(), refetchShops()])
  })

  return (
    <div className="pb-20 max-w-app mx-auto">
      {refreshing && (
        <div className="text-center text-xs text-tg-accent py-2">
          <span className="animate-spin inline-block">⟳</span> Yangilanmoqda...
        </div>
      )}

      <div className="bg-gradient-to-br from-tg-accent/20 via-tg-header to-tg-bg px-4 pt-5 pb-6 rounded-b-3xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-tg-accent flex items-center justify-center text-lg font-bold">🛒</div>
          <div>
            <h1 className="text-lg font-bold">OnBozor</h1>
            <p className="text-[11px] text-tg-muted">O'zbekiston bozori</p>
          </div>
        </div>
        <SearchBar />
      </div>

      <div className="px-4 mt-5">
        <div className="grid grid-cols-3 gap-2">
          {CATEGORIES.map((c) => (
            <Link
              key={c.slug}
              to={`/listings/${c.slug}`}
              onClick={() => haptic('impact', 'light')}
              className={`bg-gradient-to-br ${c.gradient} rounded-xl p-3 text-center transition-transform active:scale-95`}
            >
              <span className="text-2xl block">{c.emoji}</span>
              <span className="text-[10px] text-white/90 font-medium mt-1 block">{c.label}</span>
            </Link>
          ))}
          <Link
            to="/shops"
            onClick={() => haptic('impact', 'light')}
            className="bg-gradient-to-br from-tg-accent to-blue-600 rounded-xl p-3 text-center transition-transform active:scale-95"
          >
            <span className="text-2xl block">🏪</span>
            <span className="text-[10px] text-white/90 font-medium mt-1 block">Do'konlar</span>
          </Link>
        </div>
      </div>

      <PopularSection />

      <div className="px-4 mt-6">
        <div className="flex justify-between items-center mb-3">
          <h2 className="text-base font-semibold">Yangi e'lonlar</h2>
          <Link to="/search" className="text-xs text-tg-accent font-medium">Barchasi →</Link>
        </div>
        {loadingListings ? (
          <ListSkeleton count={4} />
        ) : listings?.length ? (
          <div className="grid grid-cols-2 gap-3">
            {listings.map((l) => <ProductCard key={l.id} listing={l} />)}
          </div>
        ) : (
          <div className="card text-center py-10">
            <p className="text-3xl mb-2">📢</p>
            <p className="text-sm text-tg-muted">Hozircha e'lonlar yo'q</p>
            <Link to="/add-listing" className="text-xs text-tg-accent mt-2 inline-block">Birinchi e'lonni bering →</Link>
          </div>
        )}
      </div>

      <div className="px-4 mt-6 mb-4">
        <div className="flex justify-between items-center mb-3">
          <h2 className="text-base font-semibold">Mashhur do'konlar</h2>
          <Link to="/shops" className="text-xs text-tg-accent font-medium">Barchasi →</Link>
        </div>
        {loadingShops ? (
          <div className="space-y-3">{Array.from({ length: 3 }, (_, i) => <ShopSkeleton key={i} />)}</div>
        ) : shops?.length ? (
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 snap-x">
            {shops.map((s) => (
              <div key={s.id} className="min-w-[280px] snap-start shrink-0">
                <ShopCard shop={s} />
              </div>
            ))}
          </div>
        ) : (
          <div className="card text-center py-10">
            <p className="text-3xl mb-2">🏪</p>
            <p className="text-sm text-tg-muted">Hozircha do'konlar yo'q</p>
          </div>
        )}
      </div>
    </div>
  )
}
