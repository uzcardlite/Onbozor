import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import ProductCard from '../components/ProductCard'
import ShopCard from '../components/ShopCard'
import { ListSkeleton, ShopSkeleton } from '../components/LoadingSkeleton'
import { listingsAPI, shopsAPI } from '../api/endpoints'
import { usePullRefresh } from '../hooks/usePullRefresh'

const CATEGORIES = [
  { slug: 'uyjoy', emoji: '🏠', label: 'Uy-joy' },
  { slug: 'texnika', emoji: '📱', label: 'Texnika' },
  { slug: 'avto', emoji: '🚗', label: 'Avtomobil' },
  { slug: 'moto', emoji: '🏍', label: 'Moto' },
  { slug: 'kiyim', emoji: '👕', label: 'Kiyim' },
]

export default function Home() {
  const { data: listings, isLoading: loadingListings, refetch: refetchListings } = useQuery({
    queryKey: ['listings', 'home'],
    queryFn: () => listingsAPI.list({ limit: 10 }).then((r) => r.data),
  })

  const { data: shops, isLoading: loadingShops, refetch: refetchShops } = useQuery({
    queryKey: ['shops', 'home'],
    queryFn: () => shopsAPI.list({ limit: 10 }).then((r) => r.data),
  })

  const refreshing = usePullRefresh(async () => {
    await Promise.all([refetchListings(), refetchShops()])
  })

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      {refreshing && (
        <div className="text-center text-xs text-tg-accent mb-2">⟳ Yangilanmoqda...</div>
      )}

      <SearchBar />

      <div className="grid grid-cols-5 gap-2 mt-5">
        {CATEGORIES.map((c) => (
          <Link
            key={c.slug}
            to={`/listings/${c.slug}`}
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
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {listings?.map((l) => <ProductCard key={l.id} listing={l} />)}
          </div>
        )}
        {!loadingListings && !listings?.length && (
          <p className="text-sm text-tg-muted text-center py-8">Hozircha e'lonlar yo'q</p>
        )}
      </div>

      <div className="mt-6">
        <div className="flex justify-between items-center mb-3">
          <h2 className="text-base font-semibold">Mashhur do'konlar</h2>
          <Link to="/shops" className="text-xs text-tg-accent">Barchasi →</Link>
        </div>
        {loadingShops ? (
          <div className="space-y-3">{Array.from({ length: 3 }, (_, i) => <ShopSkeleton key={i} />)}</div>
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 snap-x">
            {shops?.map((s) => (
              <div key={s.id} className="min-w-[260px] snap-start shrink-0">
                <ShopCard shop={s} />
              </div>
            ))}
          </div>
        )}
        {!loadingShops && !shops?.length && (
          <p className="text-sm text-tg-muted text-center py-8">Hozircha do'konlar yo'q</p>
        )}
      </div>
    </div>
  )
}
