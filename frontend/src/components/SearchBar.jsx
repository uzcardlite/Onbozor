import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTelegram } from '../hooks/useTelegram'

export default function SearchBar({ defaultValue = '', autoFocus = false }) {
  const [q, setQ] = useState(defaultValue)
  const [focused, setFocused] = useState(false)
  const navigate = useNavigate()
  const { haptic } = useTelegram()

  const onSubmit = (e) => {
    e.preventDefault()
    if (q.trim()) {
      haptic('impact', 'light')
      navigate(`/search?q=${encodeURIComponent(q.trim())}`)
    }
  }

  return (
    <form onSubmit={onSubmit} className="relative">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        autoFocus={autoFocus}
        placeholder="Qidirish..."
        className={`w-full bg-tg-card rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-tg-muted transition-all ${focused ? 'ring-2 ring-tg-accent' : ''}`}
      />
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-tg-muted">🔍</span>
    </form>
  )
}
