import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useInfiniteQuery } from '@tanstack/react-query'
import { useInView } from 'react-intersection-observer'
import ProductCard from '../components/ProductCard'
import FilterDrawer from '../components/FilterDrawer'
import { ListSkeleton } from '../components/LoadingSkeleton'
import { listingsAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'

const SECTION_META = {
  uyjoy: { emoji: '🏠', title: 'Uy-joy', subs: ['Sotish', 'Ijara', 'Dacha', 'Garaj'] },
  texnika: { emoji: '📱', title: 'Texnika', subs: ['Telefon', 'Noutbuk', 'Maishiy texnika', 'Boshqalar'] },
  avto: { emoji: '🚗', title: 'Avtomobil', subs: ['Yangi', 'Ishlatilgan', 'Ehtiyot qismlar'] },
  moto: { emoji: '🏍', title: 'Moto', subs: ['Skuterlar', 'Motolar'] },
  kiyim: { emoji: '👕', title: 'Kiyim', subs: ['Erkak', 'Ayol', 'Bola'] },
}

export default function SectionPage() {
  const { section } = useParams()
  const meta = SECTION_META[section] || { emoji: '📦', title: section, subs: [] }
  const [activeSub, setActiveSub] = useState(null)
  const [filterOpen, setFilterOpen] = useState(false)
  const [filters, setFilters] = useState({})
  const { haptic } = useTelegram()

  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ['section', section, activeSub, filters],
    queryFn: ({ pageParam = 1 }) =>
      listingsAPI.list({ section, category: activeSub, ...filters, page: pageParam, limit: 20 }).then((r) => r.data),
    getNextPageParam: (last, pages) => last.length === 20 ? pages.length + 1 : undefined,
  })

  const { ref } = useInView({
    onChange: (inView) => { if (inView && hasNextPage) fetchNextPage() },
  })

  const listings = data?.pages.flat() || []

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">{meta.emoji} {meta.title}</h1>
        <button onClick={() => { haptic('impact'); setFilterOpen(true) }} className="text-xs text-tg-accent">⚙️ Filter</button>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-3 -mx-4 px-4 mb-4">
        <button
          onClick={() => { haptic('selection'); setActiveSub(null) }}
          className={`px-4 py-2 rounded-full text-xs font-medium whitespace-nowrap transition shrink-0 ${!activeSub ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}
        >
          Barchasi
        </button>
        {meta.subs.map((s) => (
          <button
            key={s}
            onClick={() => { haptic('selection'); setActiveSub(activeSub === s ? null : s) }}
            className={`px-4 py-2 rounded-full text-xs font-medium whitespace-nowrap transition shrink-0 ${activeSub === s ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}
          >
            {s}
          </button>
        ))}
      </div>

      {isLoading ? (
        <ListSkeleton count={6} />
      ) : listings.length ? (
        <>
          <div className="grid grid-cols-2 gap-3">
            {listings.map((l) => <ProductCard key={l.id} listing={l} />)}
          </div>
          <div ref={ref} className="py-4 text-center">
            {isFetchingNextPage && <span className="text-xs text-tg-muted">Yuklanmoqda...</span>}
          </div>
        </>
      ) : (
        <div className="text-center py-16">
          <p className="text-3xl mb-3">{meta.emoji}</p>
          <p className="text-sm text-tg-muted">Bu bo'limda hozircha e'lon yo'q</p>
        </div>
      )}

      <FilterDrawer open={filterOpen} onClose={() => setFilterOpen(false)} filters={filters} onApply={setFilters} />
    </div>
  )
}
