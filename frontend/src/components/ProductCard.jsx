import { Link } from 'react-router-dom'
import { useTelegram } from '../hooks/useTelegram'

function formatPrice(n) {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

export default function ProductCard({ listing }) {
  const { haptic } = useTelegram()
  const img = listing.image_urls?.[0]

  return (
    <Link
      to={`/listing/${listing.id}`}
      onClick={() => haptic('impact', 'light')}
      className="card block transition-transform active:scale-[0.98]"
    >
      <div className="aspect-[4/3] bg-tg-bg relative">
        {img ? (
          <img src={img} alt="" loading="lazy" className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-3xl text-tg-muted">📷</div>
        )}
        {listing.is_promoted && (
          <span className="absolute top-2 left-2 bg-tg-yellow text-black text-[10px] font-bold px-2 py-0.5 rounded-full">TOP</span>
        )}
        {listing.status === 'pending' && (
          <span className="absolute top-2 right-2 bg-tg-yellow/80 text-black text-[10px] font-bold px-2 py-0.5 rounded-full">Kutilmoqda</span>
        )}
      </div>
      <div className="p-3">
        <p className="text-sm font-semibold text-tg-accent">{formatPrice(listing.price)} so'm</p>
        <p className="text-xs text-white mt-1 line-clamp-1">{listing.category}</p>
        <p className="text-[11px] text-tg-muted mt-1">📍 {listing.viloyat}</p>
      </div>
    </Link>
  )
}
