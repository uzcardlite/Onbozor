import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import ProductCard from '../components/ProductCard'
import { ListSkeleton } from '../components/LoadingSkeleton'
import { shopsAPI, favouritesAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'

const SECTION_LABEL = {
  uyjoy: '🏠 Uy-joy', texnika: '📱 Texnika', avto: '🚗 Avtomobil',
  moto: '🏍 Moto', kiyim: '👕 Kiyim',
}

export default function ShopDetail() {
  const { id } = useParams()
  const { haptic } = useTelegram()
  const qc = useQueryClient()

  const { data: shop, isLoading, isError, refetch } = useQuery({
    queryKey: ['shop', id],
    queryFn: () => shopsAPI.get(id).then((r) => r.data),
  })

  const favMutation = useMutation({
    mutationFn: () => favouritesAPI.toggleShop(id),
    onSuccess: (res) => {
      haptic('notification', 'success')
      const msg = res.data?.status === 'removed' ? 'Kuzatuvdan chiqarildi' : 'Kuzatuvga olindi'
      toast.success(msg)
      qc.invalidateQueries({ queryKey: ['favourites'] })
    },
    onError: () => toast.error("Xatolik yuz berdi"),
  })

  if (isLoading) {
    return (
      <div className="p-4 max-w-app mx-auto">
        <div className="bg-tg-card rounded-2xl h-24 animate-pulse mb-4" />
        <ListSkeleton count={4} />
      </div>
    )
  }

  if (isError || !shop) {
    return (
      <div className="p-4 text-center py-16 max-w-app mx-auto">
        <p className="text-3xl mb-3">😔</p>
        <p className="text-sm text-tg-muted mb-4">Do'kon topilmadi</p>
        {isError && <button onClick={() => refetch()} className="text-xs text-tg-accent">Qayta yuklash</button>}
      </div>
    )
  }

  const listings = shop.listings || []

  return (
    <div className="pb-20 max-w-app mx-auto">
      <div className="bg-tg-header p-5">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 rounded-2xl bg-tg-card flex items-center justify-center text-3xl overflow-hidden shrink-0">
            {shop.icon_url ? <img src={shop.icon_url} alt="" className="w-full h-full object-cover" /> : '🏪'}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold truncate">{shop.name}</h1>
              {shop.is_verified && <span className="text-tg-accent text-sm">✓</span>}
            </div>
            <p className="text-xs text-tg-muted mt-0.5">{SECTION_LABEL[shop.category] || shop.category}</p>
          </div>
        </div>

        <div className="flex gap-3">
          <div className="flex-1 bg-tg-bg/30 rounded-xl p-2.5 text-center">
            <p className="text-sm font-bold">{listings.length}</p>
            <p className="text-[10px] text-tg-muted">Mahsulotlar</p>
          </div>
          <div className="flex-1 bg-tg-bg/30 rounded-xl p-2.5 text-center">
            <p className="text-sm font-bold">📍</p>
            <p className="text-[10px] text-tg-muted">{shop.viloyat || 'Barcha'}</p>
          </div>
          <div className="flex-1 bg-tg-bg/30 rounded-xl p-2.5 text-center">
            <p className="text-sm font-bold">{shop.is_active ? '🟢' : '🔴'}</p>
            <p className="text-[10px] text-tg-muted">{shop.is_active ? 'Faol' : 'Nofaol'}</p>
          </div>
        </div>
      </div>

      <div className="px-4 pt-4">
        <p className="text-sm text-tg-muted mb-4">{shop.description}</p>

        <div className="flex gap-2 mb-3">
          <button
            onClick={() => { haptic('impact'); favMutation.mutate() }}
            disabled={favMutation.isPending}
            className="btn-outline flex-1 text-sm"
          >
            {favMutation.isPending ? '⏳' : '❤️'} Kuzatish
          </button>
          <button
            onClick={() => {
              haptic('impact')
              const botUser = import.meta.env.VITE_BOT_USERNAME || 'onbozorbot'
              const link = `https://t.me/${botUser}?start=shop_${shop.id}`
              const text = `🏪 ${shop.name} — ${shop.viloyat || "O'zbekiston"}`
              window.open(`https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`, '_blank')
            }}
            className="btn-outline !w-auto px-4 text-sm shrink-0"
          >
            📤
          </button>
        </div>
        <button
          onClick={() => {
            haptic('impact', 'light')
            const botUser = import.meta.env.VITE_BOT_USERNAME || 'onbozorbot'
            navigator.clipboard.writeText(`https://t.me/${botUser}?start=shop_${shop.id}`)
            toast.success('Havola nusxalandi!')
          }}
          className="text-xs text-tg-muted text-center w-full mb-6 active:text-tg-accent transition-colors"
        >
          🔗 Havolani nusxalash
        </button>

        <div className="flex justify-between items-center mb-3">
          <h3 className="text-sm font-semibold">Mahsulotlar</h3>
          <span className="text-xs text-tg-muted">{listings.length} ta</span>
        </div>

        {listings.length > 0 ? (
          <div className="grid grid-cols-2 gap-3">
            {listings.map((l) => <ProductCard key={l.id} listing={l} />)}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-3xl mb-3">📦</p>
            <p className="text-sm text-tg-muted">Hozircha mahsulotlar yo'q</p>
          </div>
        )}
      </div>
    </div>
  )
}
