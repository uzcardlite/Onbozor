import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import ProductCard from '../components/ProductCard'
import ShopCard from '../components/ShopCard'
import { ListSkeleton, ShopSkeleton } from '../components/LoadingSkeleton'
import { favouritesAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'

export default function Favourites() {
  const [tab, setTab] = useState('shops')
  const { haptic } = useTelegram()

  const { data, isLoading } = useQuery({
    queryKey: ['favourites'],
    queryFn: () => favouritesAPI.list().then((r) => r.data),
  })

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <h1 className="text-xl font-bold mb-4">❤️ Sevimlilar</h1>

      <div className="flex gap-2 mb-4">
        {[['shops', "🏪 Do'konlar"], ['listings', "📢 E'lonlar"]].map(([key, label]) => (
          <button
            key={key}
            onClick={() => { haptic('selection'); setTab(key) }}
            className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition ${tab === key ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {isLoading ? (
        tab === 'shops' ? (
          <div className="space-y-3">{Array.from({ length: 3 }, (_, i) => <ShopSkeleton key={i} />)}</div>
        ) : <ListSkeleton count={4} />
      ) : tab === 'shops' ? (
        data?.shops?.length ? (
          <div className="space-y-3">{data.shops.map((s) => <ShopCard key={s.id} shop={s} />)}</div>
        ) : (
          <div className="text-center py-16">
            <p className="text-3xl mb-3">🏪</p>
            <p className="text-sm text-tg-muted">Sevimli do'konlar yo'q</p>
          </div>
        )
      ) : data?.listings?.length ? (
        <div className="grid grid-cols-2 gap-3">
          {data.listings.map((l) => <ProductCard key={l.id} listing={l} />)}
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-3xl mb-3">📢</p>
          <p className="text-sm text-tg-muted">Saqlangan e'lonlar yo'q</p>
        </div>
      )}
    </div>
  )
}
