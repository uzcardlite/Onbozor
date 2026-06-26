import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTelegram } from '../hooks/useTelegram'

function formatPrice(n) {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

export default function ProductCard({ listing }) {
  const { haptic } = useTelegram()
  const [liked, setLiked] = useState(false)
  const img = listing.image_urls?.[0]

  const condBadge = listing.condition === 'yangi'
    ? { text: 'Yangi', cls: 'bg-tg-green/20 text-tg-green' }
    : listing.condition === 'ishlatilgan'
    ? { text: 'B/U', cls: 'bg-tg-yellow/20 text-tg-yellow' }
    : null

  const payBadge = listing.payment_type === 'nasiya'
    ? { text: 'Nasiya', cls: 'bg-purple-500/20 text-purple-400' }
    : listing.payment_type === 'ikkalasi'
    ? { text: 'Naqd/Nasiya', cls: 'bg-tg-accent/20 text-tg-accent' }
    : null

  return (
    <div className="card animate-fade-in group">
      <Link to={`/listing/${listing.id}`} onClick={() => haptic('impact', 'light')}>
        <div className="aspect-[4/3] bg-tg-bg relative overflow-hidden">
          {img ? (
            <img src={img} alt="" loading="lazy" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-3xl text-tg-muted/40">📷</div>
          )}
          {listing.is_promoted && (
            <span className="absolute top-2 left-2 bg-gradient-to-r from-tg-yellow to-orange-400 text-black text-[9px] font-bold px-2 py-0.5 rounded-md shadow-sm">
              {listing.promoted_type === 'featured' ? '⭐ Featured' : listing.promoted_type === 'urgent' ? '🔥 Shoshilinch' : '🔝 TOP'}
            </span>
          )}
          {condBadge && (
            <span className={`absolute bottom-2 left-2 text-[9px] font-bold px-2 py-0.5 rounded-md ${condBadge.cls}`}>{condBadge.text}</span>
          )}
        </div>
      </Link>

      <div className="p-2.5">
        <div className="flex justify-between items-start gap-1">
          <p className="text-sm font-bold text-tg-green">{formatPrice(listing.price)} <span className="text-[10px] font-normal text-tg-muted">so'm</span></p>
          <button
            onClick={(e) => { e.preventDefault(); haptic('impact', 'medium'); setLiked(!liked) }}
            className={`text-base transition-all duration-200 ${liked ? 'animate-pulse-heart text-tg-red' : 'text-tg-muted/40'}`}
          >
            {liked ? '❤️' : '🤍'}
          </button>
        </div>
        <p className="text-xs text-white/80 mt-1 line-clamp-1">{listing.category}</p>
        <div className="flex items-center justify-between mt-1.5">
          <p className="text-[10px] text-tg-muted">📍 {listing.viloyat}</p>
          {payBadge && <span className={`text-[8px] font-medium px-1.5 py-0.5 rounded ${payBadge.cls}`}>{payBadge.text}</span>}
        </div>
        {listing.views > 0 && (
          <p className="text-[10px] text-tg-muted/60 mt-1">👁 {listing.views}</p>
        )}
      </div>
    </div>
  )
}
