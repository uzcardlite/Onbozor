import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import ImageGallery from '../components/ImageGallery'
import ProductCard from '../components/ProductCard'
import PromoteModal from '../components/PromoteModal'
import { ListSkeleton } from '../components/LoadingSkeleton'
import { listingsAPI, favouritesAPI } from '../api/endpoints'
import ReviewSection from '../components/ReviewSection'
import { useUserStore } from '../store/useStore'
import { useTelegram } from '../hooks/useTelegram'

function formatPrice(n) {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

export default function ListingDetail() {
  const { id } = useParams()
  const { haptic } = useTelegram()
  const { user } = useUserStore()
  const qc = useQueryClient()
  const [promoteOpen, setPromoteOpen] = useState(false)

  const { data: listing, isLoading } = useQuery({
    queryKey: ['listing', id],
    queryFn: () => listingsAPI.get(id).then((r) => r.data),
  })

  const { data: similar, isLoading: loadingSimilar } = useQuery({
    queryKey: ['similar', listing?.section],
    queryFn: () => listingsAPI.list({ section: listing.section, limit: 4 }).then((r) => r.data),
    enabled: !!listing,
  })

  useEffect(() => {
    if (!listing?.category) return
    try {
      const viewed = JSON.parse(localStorage.getItem('viewed_categories') || '[]')
      viewed.push(listing.category)
      localStorage.setItem('viewed_categories', JSON.stringify(viewed.slice(-20)))
    } catch {}
  }, [listing?.category])

  const favMutation = useMutation({
    mutationFn: () => favouritesAPI.toggleListing(id),
    onSuccess: (res) => {
      haptic('notification', 'success')
      toast.success(res.data.status === 'added' ? "Sevimlilarga qo'shildi" : "Sevimlilardan o'chirildi")
      qc.invalidateQueries({ queryKey: ['favourites'] })
    },
  })

  if (isLoading) return <div className="p-4 max-w-app mx-auto"><ListSkeleton count={1} /></div>
  if (!listing) return <div className="p-4 text-center text-tg-muted">E'lon topilmadi</div>

  const condLabel = listing.condition === 'yangi' ? '🆕 Yangi' : '♻️ Ishlatilgan'
  const payLabel = { naqd: '💵 Naqd', nasiya: '💳 Nasiya', ikkalasi: '💵💳 Ikkalasi' }[listing.payment_type]

  return (
    <div className="pb-20 max-w-app mx-auto">
      <ImageGallery images={listing.image_urls} />

      <div className="px-4 pt-4">
        <div className="flex justify-between items-start mb-2">
          <p className="text-xl font-bold text-tg-accent">{formatPrice(listing.price)} so'm</p>
          <button onClick={() => { haptic('impact'); favMutation.mutate() }} className="text-2xl">
            ❤️
          </button>
        </div>

        {listing.negotiable && <p className="text-xs text-tg-yellow mb-2">Kelishiladi</p>}

        <p className="text-base font-semibold mb-1">{listing.category}{listing.subcategory ? ` → ${listing.subcategory}` : ''}</p>
        <p className="text-sm text-tg-muted mb-4">{listing.description}</p>

        <div className="grid grid-cols-2 gap-2 mb-4">
          <div className="bg-tg-card rounded-xl p-3">
            <p className="text-[10px] text-tg-muted mb-1">Holat</p>
            <p className="text-xs font-medium">{condLabel}</p>
          </div>
          <div className="bg-tg-card rounded-xl p-3">
            <p className="text-[10px] text-tg-muted mb-1">To'lov</p>
            <p className="text-xs font-medium">{payLabel}</p>
          </div>
          <div className="bg-tg-card rounded-xl p-3">
            <p className="text-[10px] text-tg-muted mb-1">Viloyat</p>
            <p className="text-xs font-medium">📍 {listing.viloyat}</p>
          </div>
          <div className="bg-tg-card rounded-xl p-3">
            <p className="text-[10px] text-tg-muted mb-1">Ko'rishlar</p>
            <p className="text-xs font-medium">👁 {listing.views}</p>
          </div>
        </div>

        <div className="flex gap-2 mb-4">
          <a
            href={`https://t.me/${listing.seller_username.replace('@', '')}`}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => haptic('impact', 'medium')}
            className="btn-primary block text-center flex-1"
          >
            📱 Bog'lanish
          </a>
          <button
            onClick={() => {
              haptic('impact')
              const botUser = import.meta.env.VITE_BOT_USERNAME || 'onbozorbot'
              const link = `https://t.me/${botUser}?start=listing_${listing.id}`
              const text = `${listing.category} — ${formatPrice(listing.price)} so'm (${listing.viloyat})`
              const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`
              window.open(shareUrl, '_blank')
            }}
            className="btn-outline !w-auto px-4 shrink-0"
          >
            📤
          </button>
        </div>
        <button
          onClick={() => {
            haptic('impact', 'light')
            const botUser = import.meta.env.VITE_BOT_USERNAME || 'onbozorbot'
            const link = `https://t.me/${botUser}?start=listing_${listing.id}`
            navigator.clipboard.writeText(link)
            toast.success('Havola nusxalandi!')
          }}
          className="text-xs text-tg-muted text-center w-full mb-6 active:text-tg-accent transition-colors"
        >
          🔗 Havolani nusxalash
        </button>

        {user && listing.user_id === user.id && !listing.is_promoted && (
          <button onClick={() => { haptic('impact'); setPromoteOpen(true) }} className="btn-outline mb-4 text-sm">
            🚀 E'lonni kuchaytirish
          </button>
        )}

        {listing.is_promoted && (
          <div className="card p-3 mb-4 flex items-center gap-2">
            <span className="text-tg-yellow">⭐</span>
            <span className="text-xs text-tg-yellow font-medium">Promosiya faol</span>
          </div>
        )}

        <ReviewSection listingId={listing.id} sellerId={listing.user_id} />

        <PromoteModal open={promoteOpen} onClose={() => setPromoteOpen(false)} listingId={listing.id} />

        {similar?.length > 0 && (
          <div className="mt-2 mb-4">
            <h3 className="text-sm font-semibold mb-3">O'xshash e'lonlar</h3>
            {loadingSimilar ? <ListSkeleton count={2} /> : (
              <div className="grid grid-cols-2 gap-3">
                {similar.filter((s) => s.id !== listing.id).slice(0, 4).map((l) => (
                  <ProductCard key={l.id} listing={l} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
