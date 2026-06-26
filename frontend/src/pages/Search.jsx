import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useInfiniteQuery } from '@tanstack/react-query'
import { useInView } from 'react-intersection-observer'
import SearchBar from '../components/SearchBar'
import FilterDrawer from '../components/FilterDrawer'
import ProductCard from '../components/ProductCard'
import ShopCard from '../components/ShopCard'
import { ListSkeleton, ShopSkeleton } from '../components/LoadingSkeleton'
import { searchAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'

const SORT_OPTIONS = [
  { value: 'newest', label: '🕐 Yangi' },
  { value: 'cheapest', label: '💰 Arzon' },
  { value: 'expensive', label: '💎 Qimmat' },
  { value: 'popular', label: '🔥 Mashhur' },
]

function getRecentSearches() {
  try { return JSON.parse(localStorage.getItem('recent_searches') || '[]') } catch { return [] }
}

function saveSearch(q) {
  if (!q?.trim()) return
  const list = getRecentSearches().filter((s) => s !== q)
  list.unshift(q)
  localStorage.setItem('recent_searches', JSON.stringify(list.slice(0, 5)))
}

function clearRecentSearches() {
  localStorage.removeItem('recent_searches')
}

export default function Search() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const q = params.get('q') || ''
  const [filterOpen, setFilterOpen] = useState(false)
  const [filters, setFilters] = useState({})
  const [sort, setSort] = useState('newest')
  const [tab, setTab] = useState('listings')
  const [showRecent, setShowRecent] = useState(!q)
  const [recentSearches, setRecentSearches] = useState(getRecentSearches())
  const { haptic } = useTelegram()

  useEffect(() => {
    if (q) {
      saveSearch(q)
      setShowRecent(false)
      setRecentSearches(getRecentSearches())
    }
  }, [q])

  const activeFilters = Object.values(filters).filter(Boolean).length

  const { data, isLoading, isError, refetch, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ['search', q, filters, sort],
    queryFn: ({ pageParam = 1 }) =>
      searchAPI.search({ q: q || undefined, ...filters, sort, page: pageParam, limit: 20 }).then((r) => r.data),
    getNextPageParam: (last, pages) => {
      const items = last?.listings || []
      return items.length >= 20 ? pages.length + 1 : undefined
    },
    enabled: !!q || activeFilters > 0,
  })

  const { ref } = useInView({
    onChange: (inView) => { if (inView && hasNextPage && !isFetchingNextPage) fetchNextPage() },
  })

  const listings = data?.pages.flatMap((p) => p.listings || []) || []
  const shops = data?.pages[0]?.shops || []
  const totalListings = data?.pages[0]?.total_listings || 0
  const totalShops = data?.pages[0]?.total_shops || 0
  const hasResults = totalListings > 0 || totalShops > 0

  const appliedFilters = Object.entries(filters)
    .filter(([, v]) => v)
    .map(([k, v]) => ({ key: k, label: v }))

  const removeFilter = (key) => {
    haptic('impact', 'light')
    setFilters((f) => { const n = { ...f }; delete n[key]; return n })
  }

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <div className="flex gap-2 mb-3">
        <div className="flex-1">
          <SearchBar
            defaultValue={q}
            autoFocus={!q}
            onFocus={() => !q && setShowRecent(true)}
          />
        </div>
        <button
          onClick={() => { haptic('impact'); setFilterOpen(true) }}
          className="w-12 h-12 bg-tg-card rounded-xl flex items-center justify-center text-lg shrink-0 relative border border-tg-border"
        >
          ⚙️
          {activeFilters > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-tg-accent rounded-full text-[9px] font-bold flex items-center justify-center">{activeFilters}</span>
          )}
        </button>
      </div>

      {showRecent && !q && recentSearches.length > 0 && (
        <div className="mb-4 animate-fade-in">
          <div className="flex justify-between items-center mb-2">
            <p className="text-xs text-tg-muted font-medium">Oxirgi qidiruvlar</p>
            <button onClick={() => { clearRecentSearches(); setRecentSearches([]); haptic('impact', 'light') }} className="text-[10px] text-tg-red">Tozalash</button>
          </div>
          <div className="flex flex-wrap gap-2">
            {recentSearches.map((s) => (
              <button
                key={s}
                onClick={() => { haptic('selection'); navigate(`/search?q=${encodeURIComponent(s)}`) }}
                className="chip chip-inactive text-[11px]"
              >
                🕐 {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {appliedFilters.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {appliedFilters.map((f) => (
            <button key={f.key} onClick={() => removeFilter(f.key)} className="chip chip-active text-[10px] flex items-center gap-1">
              {f.label} <span className="opacity-60">✕</span>
            </button>
          ))}
          <button onClick={() => { setFilters({}); haptic('impact') }} className="chip chip-inactive text-[10px]">Tozalash</button>
        </div>
      )}

      {(q || activeFilters > 0) && (
        <>
          <div className="flex gap-1.5 overflow-x-auto pb-2 mb-3 -mx-4 px-4">
            {SORT_OPTIONS.map((s) => (
              <button
                key={s.value}
                onClick={() => { haptic('selection'); setSort(s.value) }}
                className={`chip ${sort === s.value ? 'chip-active' : 'chip-inactive'}`}
              >
                {s.label}
              </button>
            ))}
          </div>

          {hasResults && (
            <div className="flex gap-2 mb-3">
              <button
                onClick={() => { haptic('selection'); setTab('listings') }}
                className={`flex-1 py-2 rounded-lg text-xs font-medium transition ${tab === 'listings' ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted border border-tg-border'}`}
              >
                📢 E'lonlar ({totalListings})
              </button>
              <button
                onClick={() => { haptic('selection'); setTab('shops') }}
                className={`flex-1 py-2 rounded-lg text-xs font-medium transition ${tab === 'shops' ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted border border-tg-border'}`}
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
                <p className="text-[11px] text-tg-muted mb-3">{totalListings} ta natija topildi</p>
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
                <p className="text-sm text-tg-muted mb-2">Hech narsa topilmadi</p>
                {q && <p className="text-xs text-tg-muted">"{q}" bo'yicha natija yo'q</p>}
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
        </>
      )}

      {!q && activeFilters === 0 && !showRecent && (
        <div className="text-center py-16">
          <p className="text-3xl mb-3">🔍</p>
          <p className="text-sm text-tg-muted">Qidirmoqchi bo'lgan narsangizni yozing</p>
        </div>
      )}

      <FilterDrawer open={filterOpen} onClose={() => setFilterOpen(false)} filters={filters} onApply={setFilters} />
    </div>
  )
}
