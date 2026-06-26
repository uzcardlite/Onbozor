import { useState } from 'react'
import { useTelegram } from '../hooks/useTelegram'

const REGIONS = [
  "Toshkent", "Samarqand", "Buxoro", "Andijon", "Farg'ona",
  "Namangan", "Qashqadaryo", "Surxondaryo", "Sirdaryo",
  "Jizzax", "Navoiy", "Xorazm", "Qoraqalpog'iston",
]

const SECTIONS = [
  { value: 'uyjoy', label: '🏠 Uy-joy' },
  { value: 'texnika', label: '📱 Texnika' },
  { value: 'avto', label: '🚗 Avtomobil' },
  { value: 'moto', label: '🏍 Moto' },
  { value: 'kiyim', label: '👕 Kiyim' },
]

export default function FilterDrawer({ open, onClose, filters, onApply }) {
  const [local, setLocal] = useState(filters)
  const { haptic } = useTelegram()

  if (!open) return null

  const set = (k, v) => setLocal((p) => ({ ...p, [k]: v }))

  return (
    <div className="fixed inset-0 z-50 flex items-end max-w-app mx-auto">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative bg-tg-card w-full rounded-t-2xl p-5 pb-8 max-h-[80vh] overflow-y-auto animate-slide-up">
        <div className="w-10 h-1 bg-tg-muted/40 rounded-full mx-auto mb-5" />
        <h3 className="text-lg font-semibold mb-4">Filter</h3>

        <div className="mb-4">
          <p className="text-xs text-tg-muted mb-2">Bo'lim</p>
          <div className="flex flex-wrap gap-2">
            {SECTIONS.map((s) => (
              <button
                key={s.value}
                onClick={() => { haptic('selection'); set('section', local.section === s.value ? null : s.value) }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${local.section === s.value ? 'bg-tg-accent text-white' : 'bg-tg-bg text-tg-muted border border-tg-border'}`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <p className="text-xs text-tg-muted mb-2">Narx oralig'i</p>
          <div className="flex gap-2">
            <input placeholder="Min" type="number" value={local.price_min || ''} onChange={(e) => set('price_min', e.target.value)} className="input-field text-sm flex-1" />
            <input placeholder="Max" type="number" value={local.price_max || ''} onChange={(e) => set('price_max', e.target.value)} className="input-field text-sm flex-1" />
          </div>
        </div>

        <div className="mb-4">
          <p className="text-xs text-tg-muted mb-2">Viloyat</p>
          <div className="flex flex-wrap gap-2">
            {REGIONS.map((r) => (
              <button
                key={r}
                onClick={() => { haptic('selection'); set('viloyat', local.viloyat === r ? null : r) }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${local.viloyat === r ? 'bg-tg-accent text-white' : 'bg-tg-bg text-tg-muted border border-tg-border'}`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <p className="text-xs text-tg-muted mb-2">Holat</p>
          <div className="flex gap-2">
            {['yangi', 'ishlatilgan'].map((c) => (
              <button
                key={c}
                onClick={() => { haptic('selection'); set('condition', local.condition === c ? null : c) }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex-1 ${local.condition === c ? 'bg-tg-accent text-white' : 'bg-tg-bg text-tg-muted border border-tg-border'}`}
              >
                {c === 'yangi' ? '🆕 Yangi' : '♻️ Ishlatilgan'}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-6">
          <p className="text-xs text-tg-muted mb-2">To'lov turi</p>
          <div className="flex gap-2">
            {['naqd', 'nasiya', 'ikkalasi'].map((p) => (
              <button
                key={p}
                onClick={() => { haptic('selection'); set('payment_type', local.payment_type === p ? null : p) }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex-1 ${local.payment_type === p ? 'bg-tg-accent text-white' : 'bg-tg-bg text-tg-muted border border-tg-border'}`}
              >
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="flex gap-3">
          <button onClick={() => { setLocal({}); haptic('impact') }} className="btn-outline flex-1">Tozalash</button>
          <button onClick={() => { onApply(local); onClose(); haptic('impact', 'medium') }} className="btn-primary flex-1">Qo'llash</button>
        </div>
      </div>
    </div>
  )
}
