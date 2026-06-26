import { Link } from 'react-router-dom'
import { useTelegram } from '../hooks/useTelegram'

const GRADIENTS = [
  'from-blue-500 to-cyan-500',
  'from-purple-500 to-pink-500',
  'from-orange-500 to-red-500',
  'from-green-500 to-emerald-500',
  'from-indigo-500 to-violet-500',
]

export default function ShopCard({ shop }) {
  const { haptic } = useTelegram()
  const grad = GRADIENTS[shop.name.length % GRADIENTS.length]
  const initials = shop.name.slice(0, 2).toUpperCase()

  return (
    <Link
      to={`/shop/${shop.id}`}
      onClick={() => haptic('impact', 'light')}
      className="card flex items-center gap-3 p-3 transition-all duration-150 active:scale-[0.98] animate-fade-in"
    >
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-sm font-bold text-white shrink-0 overflow-hidden bg-gradient-to-br ${grad}`}>
        {shop.icon_url ? (
          <img src={shop.icon_url} alt="" className="w-full h-full object-cover" />
        ) : initials}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <p className="text-sm font-semibold text-white truncate">{shop.name}</p>
          {shop.is_verified && <span className="text-tg-accent text-xs">✓</span>}
          {shop.is_active && <span className="w-1.5 h-1.5 rounded-full bg-tg-green shrink-0" />}
        </div>
        <p className="text-xs text-tg-muted mt-0.5 line-clamp-1">{shop.description}</p>
      </div>
      <div className="text-right shrink-0">
        <p className="text-[10px] text-tg-muted">📍 {shop.viloyat || 'Barcha'}</p>
      </div>
    </Link>
  )
}
