import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { promotionsAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'

const PROMO_TYPES = [
  { type: 'top', emoji: '🔝', label: 'Tepaga chiqarish', price: '15 000', duration: '24 soat', desc: "E'loningiz ro'yxat yuqorisida ko'rinadi" },
  { type: 'featured', emoji: '⭐', label: 'Featured', price: '25 000', duration: '48 soat', desc: "Bosh sahifada alohida ko'rinadi" },
  { type: 'urgent', emoji: '🔥', label: 'Shoshilinch', price: '10 000', duration: '24 soat', desc: "'Shoshilinch' badgesi qo'shiladi" },
]

export default function PromoteModal({ open, onClose, listingId }) {
  const [selected, setSelected] = useState(null)
  const [method, setMethod] = useState(null)
  const { haptic } = useTelegram()

  const mutation = useMutation({
    mutationFn: () => promotionsAPI.initiate({ listing_id: listingId, type: selected, method }),
    onSuccess: (res) => {
      haptic('notification', 'success')
      if (res.data.payment_url) {
        window.open(res.data.payment_url, '_blank')
      }
      toast.success("To'lov sahifasiga yo'naltirildi")
      onClose()
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Xatolik'),
  })

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end max-w-app mx-auto">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative bg-tg-card w-full rounded-t-2xl p-5 pb-8 animate-slide-up">
        <div className="w-10 h-1 bg-tg-muted/30 rounded-full mx-auto mb-4" />
        <h3 className="text-lg font-bold mb-4">🚀 E'lonni kuchaytirish</h3>

        <div className="space-y-2 mb-5">
          {PROMO_TYPES.map((p) => (
            <button
              key={p.type}
              onClick={() => { haptic('selection'); setSelected(p.type) }}
              className={`w-full p-4 rounded-xl text-left transition-all ${selected === p.type ? 'bg-tg-accent/10 border-2 border-tg-accent' : 'bg-tg-bg border-2 border-transparent'}`}
            >
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-semibold">{p.emoji} {p.label}</span>
                <span className="text-sm font-bold text-tg-green">{p.price} so'm</span>
              </div>
              <p className="text-[11px] text-tg-muted">{p.desc} · {p.duration}</p>
            </button>
          ))}
        </div>

        {selected && (
          <div className="animate-fade-in">
            <p className="text-xs text-tg-muted mb-2">To'lov usuli:</p>
            <div className="flex gap-2 mb-4">
              {[['payme', '💳 Payme'], ['click', '💳 Click']].map(([v, l]) => (
                <button
                  key={v}
                  onClick={() => { haptic('selection'); setMethod(v) }}
                  className={`flex-1 py-3 rounded-lg text-sm font-medium transition ${method === v ? 'bg-tg-accent text-white' : 'bg-tg-bg text-tg-muted border border-tg-border'}`}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>
        )}

        <button
          onClick={() => mutation.mutate()}
          disabled={!selected || !method || mutation.isPending}
          className={`btn-primary ${!selected || !method ? 'opacity-40' : ''}`}
        >
          {mutation.isPending ? '⏳ Kutilmoqda...' : '💳 To\'lash va faollashtirish'}
        </button>
      </div>
    </div>
  )
}
