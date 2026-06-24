import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useInfiniteQuery } from '@tanstack/react-query'
import { useInView } from 'react-intersection-observer'
import SearchBar from '../components/SearchBar'
import FilterDrawer from '../components/FilterDrawer'
import ProductCard from '../components/ProductCard'
import { ListSkeleton } from '../components/LoadingSkeleton'
import { searchAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'

export default function Search() {
  const [params] = useSearchParams()
  const q = params.get('q') || ''
  const [filterOpen, setFilterOpen] = useState(false)
  const [filters, setFilters] = useState({})
  const { haptic } = useTelegram()

  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ['search', q, filters],
    queryFn: ({ pageParam = 1 }) =>
      searchAPI.search({ q, ...filters, page: pageParam, limit: 20 }).then((r) => r.data),
    getNextPageParam: (last, pages) =>
      last.listings.length === 20 ? pages.length + 1 : undefined,
  })

  const { ref } = useInView({
    onChange: (inView) => { if (inView && hasNextPage) fetchNextPage() },
  })

  const listings = data?.pages.flatMap((p) => p.listings) || []

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <div className="flex gap-2 mb-4">
        <div className="flex-1"><SearchBar defaultValue={q} autoFocus={!q} /></div>
        <button
          onClick={() => { haptic('impact'); setFilterOpen(true) }}
          className="w-12 h-12 bg-tg-card rounded-xl flex items-center justify-center text-lg shrink-0"
        >
          ⚙️
        </button>
      </div>

      {isLoading ? (
        <ListSkeleton count={6} />
      ) : listings.length ? (
        <>
          <p className="text-xs text-tg-muted mb-3">{data?.pages[0]?.total_listings || 0} ta natija</p>
          <div className="grid grid-cols-2 gap-3">
            {listings.map((l) => <ProductCard key={l.id} listing={l} />)}
          </div>
          <div ref={ref} className="py-4 text-center">
            {isFetchingNextPage && <span className="text-xs text-tg-muted">Yuklanmoqda...</span>}
          </div>
        </>
      ) : (
        <div className="text-center py-16">
          <p className="text-3xl mb-3">🔍</p>
          <p className="text-sm text-tg-muted">Natija topilmadi</p>
        </div>
      )}

      <FilterDrawer open={filterOpen} onClose={() => setFilterOpen(false)} filters={filters} onApply={setFilters} />
    </div>
  )
}
