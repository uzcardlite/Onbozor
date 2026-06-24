import { Link } from 'react-router-dom'
import { useTelegram } from '../hooks/useTelegram'

export default function ShopCard({ shop }) {
  const { haptic } = useTelegram()

  return (
    <Link
      to={`/shop/${shop.id}`}
      onClick={() => haptic('impact', 'light')}
      className="card flex items-center gap-3 p-3 transition-transform active:scale-[0.98]"
    >
      <div className="w-12 h-12 rounded-xl bg-tg-bg flex items-center justify-center text-2xl shrink-0 overflow-hidden">
        {shop.icon_url ? (
          <img src={shop.icon_url} alt="" className="w-full h-full object-cover" />
        ) : '🏪'}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-white truncate">{shop.name}</p>
        <p className="text-xs text-tg-muted mt-0.5 truncate">{shop.description}</p>
        <p className="text-[11px] text-tg-muted mt-0.5">📍 {shop.viloyat || "Barcha viloyatlar"}</p>
      </div>
      {shop.is_verified && <span className="text-tg-accent text-lg shrink-0">✓</span>}
    </Link>
  )
}
