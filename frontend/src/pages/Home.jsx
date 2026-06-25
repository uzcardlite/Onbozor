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
  { slug: 'uyjoy', emoji: '🏠', label: 'Uy-joy' },
  { slug: 'texnika', emoji: '📱', label: 'Texnika' },
  { slug: 'avto', emoji: '🚗', label: 'Avtomobil' },
  { slug: 'moto', emoji: '🏍', label: 'Moto' },
  { slug: 'kiyim', emoji: '👕', label: 'Kiyim' },
]

export default function Home() {
  const { haptic } = useTelegram()

  const { data: listings, isLoading: loadingListings, isError: errorListings, refetch: refetchListings } = useQuery({
    queryKey: ['listings', 'home'],
    queryFn: () => listingsAPI.list({ limit: 10 }).then((r) => r.data),
    retry: 1,
  })

  const { data: shops, isLoading: loadingShops, isError: errorShops, refetch: refetchShops } = useQuery({
    queryKey: ['shops', 'home'],
    queryFn: () => shopsAPI.list({ limit: 10 }).then((r) => r.data),
    retry: 1,
  })

  const refreshing = usePullRefresh(async () => {
    await Promise.all([refetchListings(), refetchShops()])
  })

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      {refreshing && (
        <div className="text-center text-xs text-tg-accent mb-2">
          <span className="animate-spin inline-block">⟳</span> Yangilanmoqda...
        </div>
      )}

      <SearchBar />

      <div className="grid grid-cols-5 gap-2 mt-5">
        {CATEGORIES.map((c) => (
          <Link
            key={c.slug}
            to={`/listings/${c.slug}`}
            onClick={() => haptic('impact', 'light')}
            className="flex flex-col items-center gap-1.5 bg-tg-card rounded-xl py-3 transition-transform active:scale-95"
          >
            <span className="text-2xl">{c.emoji}</span>
            <span className="text-[10px] text-tg-muted font-medium">{c.label}</span>
          </Link>
        ))}
      </div>

      <div className="mt-6">
        <div className="flex justify-between items-center mb-3">
          <h2 className="text-base font-semibold">Yangi e'lonlar</h2>
          <Link to="/search" className="text-xs text-tg-accent">Barchasi →</Link>
        </div>
        {loadingListings ? (
          <ListSkeleton count={4} />
        ) : errorListings ? (
          <div className="text-center py-8">
            <p className="text-sm text-tg-muted mb-2">Ma'lumot yuklanmadi</p>
            <button onClick={() => refetchListings()} className="text-xs text-tg-accent">Qayta yuklash</button>
          </div>
        ) : listings?.length ? (
          <div className="grid grid-cols-2 gap-3">
            {listings.map((l) => <ProductCard key={l.id} listing={l} />)}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-3xl mb-2">📢</p>
            <p className="text-sm text-tg-muted">Hozircha e'lonlar yo'q</p>
          </div>
        )}
      </div>

      <div className="mt-6 mb-4">
        <div className="flex justify-between items-center mb-3">
          <h2 className="text-base font-semibold">Mashhur do'konlar</h2>
          <Link to="/shops" className="text-xs text-tg-accent">Barchasi →</Link>
        </div>
        {loadingShops ? (
          <div className="space-y-3">{Array.from({ length: 3 }, (_, i) => <ShopSkeleton key={i} />)}</div>
        ) : errorShops ? (
          <div className="text-center py-8">
            <p className="text-sm text-tg-muted mb-2">Ma'lumot yuklanmadi</p>
            <button onClick={() => refetchShops()} className="text-xs text-tg-accent">Qayta yuklash</button>
          </div>
        ) : shops?.length ? (
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 snap-x">
            {shops.map((s) => (
              <div key={s.id} className="min-w-[260px] snap-start shrink-0">
                <ShopCard shop={s} />
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-3xl mb-2">🏪</p>
            <p className="text-sm text-tg-muted">Hozircha do'konlar yo'q</p>
          </div>
        )}
      </div>
    </div>
  )
}
