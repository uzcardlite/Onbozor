import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { reviewsAPI } from '../api/endpoints'
import { useUserStore } from '../store/useStore'
import { useTelegram } from '../hooks/useTelegram'

function Stars({ rating, size = 'text-sm', onSelect = null }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <button
          key={i}
          onClick={() => onSelect?.(i)}
          disabled={!onSelect}
          className={`${size} transition-transform ${onSelect ? 'active:scale-125' : ''} ${i <= rating ? 'text-tg-yellow' : 'text-tg-muted/30'}`}
        >
          ★
        </button>
      ))}
    </div>
  )
}

function ReviewCard({ review }) {
  const initial = review.reviewer_name?.charAt(0)?.toUpperCase() || '?'
  return (
    <div className="card p-3 animate-fade-in">
      <div className="flex items-center gap-2.5 mb-2">
        <div className="w-8 h-8 rounded-full bg-tg-accent/20 flex items-center justify-center text-xs font-bold text-tg-accent shrink-0">
          {initial}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium truncate">{review.reviewer_name}</p>
          <Stars rating={review.rating} size="text-[10px]" />
        </div>
        <p className="text-[10px] text-tg-muted shrink-0">
          {new Date(review.created_at).toLocaleDateString('uz')}
        </p>
      </div>
      {review.comment && <p className="text-xs text-tg-muted ml-10">{review.comment}</p>}
    </div>
  )
}

export default function ReviewSection({ listingId, sellerId }) {
  const [showForm, setShowForm] = useState(false)
  const [rating, setRating] = useState(0)
  const [comment, setComment] = useState('')
  const { haptic } = useTelegram()
  const { token } = useUserStore()
  const qc = useQueryClient()
  const isDemo = !token || token === 'demo-token'

  const { data: reviews, isLoading } = useQuery({
    queryKey: ['reviews', listingId],
    queryFn: () => reviewsAPI.byListing(listingId).then((r) => r.data),
    enabled: !!listingId,
  })

  const { data: sellerRating } = useQuery({
    queryKey: ['seller-rating', sellerId],
    queryFn: () => reviewsAPI.byUser(sellerId).then((r) => r.data),
    enabled: !!sellerId,
  })

  const mutation = useMutation({
    mutationFn: () => reviewsAPI.create({ listing_id: listingId, rating, comment: comment || null }),
    onSuccess: () => {
      haptic('notification', 'success')
      toast.success('Reyting qoldirildi!')
      setShowForm(false)
      setRating(0)
      setComment('')
      qc.invalidateQueries({ queryKey: ['reviews', listingId] })
      qc.invalidateQueries({ queryKey: ['seller-rating', sellerId] })
    },
    onError: (err) => {
      const msg = err.response?.data?.detail || 'Xatolik yuz berdi'
      toast.error(msg)
    },
  })

  const avg = sellerRating?.avg_rating || 0
  const total = sellerRating?.total_reviews || 0

  return (
    <div className="mt-4">
      {sellerId && (
        <div className="card p-3 mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Stars rating={Math.round(avg)} size="text-base" />
            <span className="text-sm font-bold">{avg > 0 ? avg.toFixed(1) : '—'}</span>
          </div>
          <span className="text-xs text-tg-muted">{total} ta izoh</span>
          {avg >= 4.5 && total >= 3 && (
            <span className="text-[9px] bg-tg-green/15 text-tg-green px-2 py-0.5 rounded-md font-medium">Ishonchli ✓</span>
          )}
        </div>
      )}

      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-semibold">Izohlar</h3>
        {!isDemo && !showForm && (
          <button onClick={() => { haptic('impact'); setShowForm(true) }} className="text-xs text-tg-accent font-medium">
            + Reyting qoldirish
          </button>
        )}
      </div>

      {showForm && (
        <div className="card p-4 mb-3 animate-slide-up">
          <p className="text-xs text-tg-muted mb-2">Baholang:</p>
          <div className="flex justify-center mb-3">
            <Stars rating={rating} size="text-2xl" onSelect={(r) => { haptic('selection'); setRating(r) }} />
          </div>
          <textarea
            placeholder="Izoh (ixtiyoriy)"
            rows={2}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="input-field text-xs mb-3 resize-none"
          />
          <div className="flex gap-2">
            <button onClick={() => setShowForm(false)} className="btn-outline flex-1 text-xs !py-2">Bekor</button>
            <button
              onClick={() => mutation.mutate()}
              disabled={!rating || mutation.isPending}
              className={`btn-primary flex-1 text-xs !py-2 ${!rating ? 'opacity-40' : ''}`}
            >
              {mutation.isPending ? '⏳' : '✅ Yuborish'}
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">{Array.from({ length: 3 }, (_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}</div>
      ) : reviews?.length ? (
        <div className="space-y-2">
          {reviews.map((r) => <ReviewCard key={r.id} review={r} />)}
        </div>
      ) : (
        <div className="text-center py-6">
          <p className="text-2xl mb-1">⭐</p>
          <p className="text-xs text-tg-muted">Hali izohlar yo'q</p>
        </div>
      )}
    </div>
  )
}

export { Stars }
