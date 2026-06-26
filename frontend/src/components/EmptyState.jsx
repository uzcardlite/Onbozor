import { Link } from 'react-router-dom'

const PRESETS = {
  listings: { icon: '📢', title: "Hali e'lonlar yo'q", sub: "Birinchi bo'lib e'lon bering!", link: '/add-listing', linkText: "E'lon berish →" },
  shops: { icon: '🏪', title: "Hozircha do'konlar yo'q", sub: "Birinchi do'konni oching!", link: '/open-shop', linkText: "Do'kon ochish →" },
  favourites: { icon: '❤️', title: "Sevimlilar bo'sh", sub: "E'lonlarni ♥ bosib saqlang!", link: '/', linkText: "Bozorga o'tish →" },
  messages: { icon: '💬', title: "Hali xabarlar yo'q", sub: "Sotuvchi bilan bog'laning!", link: '/', linkText: "E'lonlarga o'tish →" },
  search: { icon: '🔎', title: "Hech narsa topilmadi", sub: "Boshqa kalit so'z kiriting" },
  reviews: { icon: '⭐', title: "Hali izohlar yo'q", sub: "Birinchi bo'lib baho bering!" },
  error: { icon: '⚠️', title: "Xatolik yuz berdi", sub: "Qayta urinib ko'ring" },
  offline: { icon: '📡', title: "Internet aloqasi yo'q", sub: "Ulanishni tekshiring" },
  notfound: { icon: '🔍', title: "Sahifa topilmadi", sub: "Bu sahifa mavjud emas" },
}

export default function EmptyState({ type, icon, title, sub, link, linkText, onRetry }) {
  const preset = PRESETS[type] || {}
  const i = icon || preset.icon || '📦'
  const t = title || preset.title || 'Bo\'sh'
  const s = sub || preset.sub
  const l = link || preset.link
  const lt = linkText || preset.linkText

  return (
    <div className="text-center py-16 animate-fade-in">
      <div className="text-5xl mb-4">{i}</div>
      <h3 className="text-base font-semibold mb-1">{t}</h3>
      {s && <p className="text-xs text-tg-muted mb-4">{s}</p>}
      {l && lt && <Link to={l} className="text-xs text-tg-accent font-medium">{lt}</Link>}
      {onRetry && (
        <button onClick={onRetry} className="text-xs text-tg-accent font-medium mt-2 block mx-auto">🔄 Qayta yuklash</button>
      )}
    </div>
  )
}
