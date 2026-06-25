import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useInfiniteQuery } from '@tanstack/react-query'
import { useInView } from 'react-intersection-observer'
import SearchBar from '../components/SearchBar'
import FilterDrawer from '../components/FilterDrawer'
import ProductCard from '../components/ProductCard'
import ShopCard from '../components/ShopCard'
import { ListSkeleton, ShopSkeleton } from '../components/LoadingSkeleton'
import { searchAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'

export default function Search() {
  const [params] = useSearchParams()
  const q = params.get('q') || ''
  const [filterOpen, setFilterOpen] = useState(false)
  const [filters, setFilters] = useState({})
  const [tab, setTab] = useState('listings')
  const { haptic } = useTelegram()

  const activeFilters = Object.values(filters).filter(Boolean).length

  const { data, isLoading, isError, refetch, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ['search', q, filters],
    queryFn: ({ pageParam = 1 }) =>
      searchAPI.search({ q: q || undefined, ...filters, page: pageParam, limit: 20 }).then((r) => r.data),
    getNextPageParam: (last, pages) => {
      const items = last?.listings || []
      return items.length >= 20 ? pages.length + 1 : undefined
    },
  })

  const { ref } = useInView({
    onChange: (inView) => { if (inView && hasNextPage && !isFetchingNextPage) fetchNextPage() },
  })

  const listings = data?.pages.flatMap((p) => p.listings || []) || []
  const shops = data?.pages[0]?.shops || []
  const totalListings = data?.pages[0]?.total_listings || 0
  const totalShops = data?.pages[0]?.total_shops || 0

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <div className="flex gap-2 mb-4">
        <div className="flex-1"><SearchBar defaultValue={q} autoFocus={!q} /></div>
        <button
          onClick={() => { haptic('impact'); setFilterOpen(true) }}
          className="w-12 h-12 bg-tg-card rounded-xl flex items-center justify-center text-lg shrink-0 relative"
        >
          ⚙️
          {activeFilters > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-tg-accent rounded-full text-[9px] font-bold flex items-center justify-center">
              {activeFilters}
            </span>
          )}
        </button>
      </div>

      {(totalListings > 0 || totalShops > 0) && (
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => { haptic('selection'); setTab('listings') }}
            className={`flex-1 py-2 rounded-xl text-xs font-medium transition ${tab === 'listings' ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}
          >
            📢 E'lonlar ({totalListings})
          </button>
          <button
            onClick={() => { haptic('selection'); setTab('shops') }}
            className={`flex-1 py-2 rounded-xl text-xs font-medium transition ${tab === 'shops' ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}
          >
            🏪 Do'konlar ({totalShops})
          </button>
        </div>
      )}

      {isLoading ? (
        tab === 'listings' ? <ListSkeleton count={6} /> : (
          <div className="space-y-3">{Array.from({ length: 4 }, (_, i) => <ShopSkeleton key={i} />)}</div>
        )
      ) : isError ? (
        <div className="text-center py-16">
          <p className="text-3xl mb-3">⚠️</p>
          <p className="text-sm text-tg-muted mb-4">Qidirishda xatolik</p>
          <button onClick={() => refetch()} className="text-xs text-tg-accent">Qayta urinish</button>
        </div>
      ) : tab === 'listings' ? (
        listings.length ? (
          <>
            <div className="grid grid-cols-2 gap-3">
              {listings.map((l) => <ProductCard key={l.id} listing={l} />)}
            </div>
            <div ref={ref} className="py-4 text-center">
              {isFetchingNextPage && (
                <span className="text-xs text-tg-muted">Yuklanmoqda...</span>
              )}
            </div>
          </>
        ) : (
          <div className="text-center py-16">
            <p className="text-3xl mb-3">🔍</p>
            <p className="text-sm text-tg-muted mb-2">Hech narsa topilmadi</p>
            {q && <p className="text-xs text-tg-muted">"{q}" bo'yicha natija yo'q</p>}
            {activeFilters > 0 && (
              <button onClick={() => { setFilters({}); haptic('impact') }} className="text-xs text-tg-accent mt-3">
                Filtrlarni tozalash
              </button>
            )}
          </div>
        )
      ) : shops.length ? (
        <div className="space-y-3">
          {shops.map((s) => <ShopCard key={s.id} shop={s} />)}
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-3xl mb-3">🏪</p>
          <p className="text-sm text-tg-muted">Do'konlar topilmadi</p>
        </div>
      )}

      <FilterDrawer open={filterOpen} onClose={() => setFilterOpen(false)} filters={filters} onApply={setFilters} />
    </div>
  )
}
