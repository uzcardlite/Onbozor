import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import ProductCard from '../components/ProductCard'
import { ListSkeleton } from '../components/LoadingSkeleton'
import { shopsAPI, favouritesAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'

export default function ShopDetail() {
  const { id } = useParams()
  const { haptic } = useTelegram()
  const qc = useQueryClient()

  const { data: shop, isLoading } = useQuery({
    queryKey: ['shop', id],
    queryFn: () => shopsAPI.get(id).then((r) => r.data),
  })

  const favMutation = useMutation({
    mutationFn: () => favouritesAPI.toggleShop(id),
    onSuccess: (res) => {
      haptic('notification', 'success')
      toast.success(res.data.status === 'added' ? 'Kuzatuvga olindi' : 'Kuzatuvdan chiqarildi')
      qc.invalidateQueries({ queryKey: ['favourites'] })
    },
  })

  if (isLoading) return <div className="p-4 max-w-app mx-auto"><ListSkeleton /></div>
  if (!shop) return <div className="p-4 text-center text-tg-muted">Do'kon topilmadi</div>

  return (
    <div className="pb-20 max-w-app mx-auto">
      <div className="bg-tg-header p-5 flex items-center gap-4">
        <div className="w-16 h-16 rounded-2xl bg-tg-card flex items-center justify-center text-3xl overflow-hidden shrink-0">
          {shop.icon_url ? <img src={shop.icon_url} alt="" className="w-full h-full object-cover" /> : '🏪'}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold truncate">{shop.name}</h1>
            {shop.is_verified && <span className="text-tg-accent">✓</span>}
          </div>
          <p className="text-xs text-tg-muted mt-0.5">📍 {shop.viloyat || 'Barcha viloyatlar'}</p>
          <p className="text-xs text-tg-muted">📦 {shop.listings?.length || 0} ta mahsulot</p>
        </div>
      </div>

      <div className="px-4 pt-4">
        <p className="text-sm text-tg-muted mb-4">{shop.description}</p>

        <button onClick={() => { haptic('impact'); favMutation.mutate() }} className="btn-outline mb-6 text-sm">
          ❤️ Kuzatish
        </button>

        {shop.listings?.length > 0 ? (
          <>
            <h3 className="text-sm font-semibold mb-3">Mahsulotlar</h3>
            <div className="grid grid-cols-2 gap-3">
              {shop.listings.map((l) => <ProductCard key={l.id} listing={l} />)}
            </div>
          </>
        ) : (
          <p className="text-sm text-tg-muted text-center py-8">Hozircha mahsulotlar yo'q</p>
        )}
      </div>
    </div>
  )
}
