import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import ShopCard from '../components/ShopCard'
import { ShopSkeleton } from '../components/LoadingSkeleton'
import { shopsAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'

const TABS = [
  { slug: null, label: 'Barchasi' },
  { slug: 'uyjoy', label: '🏠 Uy-joy' },
  { slug: 'texnika', label: '📱 Texnika' },
  { slug: 'avto', label: '🚗 Avto' },
  { slug: 'moto', label: '🏍 Moto' },
  { slug: 'kiyim', label: '👕 Kiyim' },
]

export default function Shops() {
  const [tab, setTab] = useState(null)
  const { haptic } = useTelegram()

  const { data: shops, isLoading, isError, refetch } = useQuery({
    queryKey: ['shops', tab],
    queryFn: () => shopsAPI.list({ category: tab }).then((r) => r.data),
  })

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold">🏪 Do'konlar</h1>
        <Link to="/open-shop" className="text-xs text-tg-accent">+ Do'kon ochish</Link>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-3 -mx-4 px-4 mb-4">
        {TABS.map((t) => (
          <button
            key={t.label}
            onClick={() => { haptic('selection'); setTab(t.slug) }}
            className={`px-4 py-2 rounded-full text-xs font-medium whitespace-nowrap transition shrink-0 ${tab === t.slug ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">{Array.from({ length: 5 }, (_, i) => <ShopSkeleton key={i} />)}</div>
      ) : isError ? (
        <div className="text-center py-16">
          <p className="text-3xl mb-3">⚠️</p>
          <p className="text-sm text-tg-muted mb-4">Ma'lumot olishda xatolik</p>
          <button onClick={() => refetch()} className="text-xs text-tg-accent">Qayta yuklash</button>
        </div>
      ) : shops?.length ? (
        <div className="space-y-3">
          {shops.map((s) => <ShopCard key={s.id} shop={s} />)}
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-3xl mb-3">🏪</p>
          <p className="text-sm text-tg-muted mb-4">Hozircha do'konlar yo'q</p>
          <Link to="/open-shop" className="text-sm text-tg-accent">Birinchi do'konni oching →</Link>
        </div>
      )}
    </div>
  )
}
