import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../store/useStore'
import { useTelegram } from '../hooks/useTelegram'

const REGIONS = [
  "Toshkent", "Samarqand", "Buxoro", "Andijon", "Farg'ona",
  "Namangan", "Qashqadaryo", "Surxondaryo", "Sirdaryo",
  "Jizzax", "Navoiy", "Xorazm", "Qoraqalpog'iston",
]

const SLIDES = [
  {
    emoji: '🛍',
    bg: 'from-blue-600 to-cyan-500',
    title: 'OnBozor ga xush kelibsiz!',
    desc: "O'zbekistonning eng yirik Telegram marketplace. Xarid qiling, soting — barchasi bir joyda!",
    features: ['📦 50,000+ mahsulot', '🏪 1,000+ do\'kon', '🇺🇿 13 ta viloyat'],
  },
  {
    emoji: '📢',
    bg: 'from-violet-600 to-purple-500',
    title: "E'lon bering, tez soting!",
    desc: 'Minglab xaridorlar sizni kutmoqda. Bepul e\'lon bering — 5 ta bo\'limda!',
    features: ['🏠 Uy-joy', '📱 Texnika', '🚗 Avtomobil'],
  },
  {
    emoji: '🏪',
    bg: 'from-emerald-600 to-green-500',
    title: "Do'kon oching, biznes quring!",
    desc: "Rasmiy do'kon oching, ishonchli sotuvchi bo'ling va daromad oling.",
    features: ['✅ Verified badge', '🚀 Promosiya', '👥 Referral 5% bonus'],
  },
]

export default function Onboarding() {
  const [step, setStep] = useState(0)
  const [region, setRegion] = useState(null)
  const [direction, setDirection] = useState(1)
  const { setOnboarded, setRegion: saveRegion } = useAppStore()
  const navigate = useNavigate()
  const { haptic } = useTelegram()
  const touchStartX = useRef(0)

  const goTo = (next) => {
    setDirection(next > step ? 1 : -1)
    setStep(next)
    haptic('impact', 'light')
  }

  const finish = () => {
    if (!region) return
    saveRegion(region)
    setOnboarded()
    haptic('notification', 'success')
    navigate('/')
  }

  const handleTouchStart = (e) => { touchStartX.current = e.touches[0].clientX }
  const handleTouchEnd = (e) => {
    const diff = e.changedTouches[0].clientX - touchStartX.current
    if (Math.abs(diff) < 50) return
    if (diff < 0 && step < 2) goTo(step + 1)
    if (diff > 0 && step > 0) goTo(step - 1)
  }

  const slide = step < 3 ? SLIDES[step] : null

  return (
    <div className="min-h-screen bg-tg-bg flex flex-col max-w-app mx-auto" onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}>
      {step < 3 ? (
        <div className="flex-1 flex flex-col animate-fade-in" key={step}>
          <div className={`bg-gradient-to-br ${slide.bg} px-6 pt-16 pb-12 rounded-b-[2rem] flex flex-col items-center`}>
            <div className="w-24 h-24 rounded-3xl bg-white/20 backdrop-blur flex items-center justify-center text-5xl mb-6 shadow-xl">
              {slide.emoji}
            </div>
            <h1 className="text-2xl font-bold text-center mb-2">{slide.title}</h1>
            <p className="text-sm text-white/80 text-center leading-relaxed max-w-[280px]">{slide.desc}</p>
          </div>

          <div className="flex-1 px-6 pt-8">
            <div className="space-y-3">
              {slide.features.map((f, i) => (
                <div key={i} className="card p-3.5 flex items-center gap-3 animate-slide-left" style={{ animationDelay: `${i * 80}ms` }}>
                  <span className="text-xl">{f.split(' ')[0]}</span>
                  <span className="text-sm">{f.split(' ').slice(1).join(' ')}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="px-6 pb-8">
            <div className="flex justify-center gap-2 mb-5">
              {[0, 1, 2].map((i) => (
                <button key={i} onClick={() => goTo(i)} className={`h-1.5 rounded-full transition-all duration-300 ${i === step ? 'w-8 bg-tg-accent' : i < step ? 'w-4 bg-tg-accent/40' : 'w-4 bg-tg-muted/20'}`} />
              ))}
            </div>
            <button onClick={() => goTo(step + 1)} className="btn-primary">
              {step === 2 ? 'Boshlash 🚀' : 'Keyingi →'}
            </button>
            {step > 0 && (
              <button onClick={() => goTo(step - 1)} className="text-xs text-tg-muted text-center w-full mt-3">← Orqaga</button>
            )}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col px-6 pt-8 animate-fade-in">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-tg-accent to-blue-600 flex items-center justify-center text-3xl mx-auto mb-4 shadow-lg shadow-tg-accent/20">📍</div>
            <h1 className="text-2xl font-bold mb-1">Viloyatingiz</h1>
            <p className="text-sm text-tg-muted">Sizga yaqin e'lonlarni ko'rsatamiz</p>
          </div>

          <div className="flex-1 overflow-y-auto">
            <div className="grid grid-cols-2 gap-2">
              {REGIONS.map((r) => (
                <button key={r} onClick={() => { haptic('selection'); setRegion(r) }}
                  className={`py-3.5 rounded-xl text-sm font-medium transition-all duration-200 ${region === r ? 'bg-tg-accent text-white shadow-lg shadow-tg-accent/20 scale-[1.02]' : 'bg-tg-card text-tg-muted border border-tg-border active:scale-95'}`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div className="py-6">
            <button onClick={finish} disabled={!region} className={`btn-primary ${!region ? 'opacity-30' : ''}`}>
              Boshlash 🚀
            </button>
            <button onClick={() => goTo(2)} className="text-xs text-tg-muted text-center w-full mt-3">← Orqaga</button>
          </div>
        </div>
      )}
    </div>
  )
}
