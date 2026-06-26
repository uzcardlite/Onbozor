import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../store/useStore'
import { useTelegram } from '../hooks/useTelegram'

const REGIONS = [
  "Toshkent", "Samarqand", "Buxoro", "Andijon", "Farg'ona",
  "Namangan", "Qashqadaryo", "Surxondaryo", "Sirdaryo",
  "Jizzax", "Navoiy", "Xorazm", "Qoraqalpog'iston",
]

const slides = [
  {
    emoji: '🛒',
    title: 'OnBozor nima?',
    desc: "O'zbekiston uchun Telegram ichida ishlaydigan mahalliy e'lonlar va do'konlar platformasi.",
  },
  {
    emoji: '⚡',
    title: 'Qanday ishlaydi?',
    items: [
      { icon: '📢', text: "E'lon bering — minglab xaridorlarga yeting" },
      { icon: '🏪', text: "Do'kon oching — mahsulotlaringizni soting" },
      { icon: '👥', text: "Do'stlarni taklif qiling — 5% bonus oling" },
    ],
  },
]

export default function Onboarding() {
  const [step, setStep] = useState(0)
  const [region, setRegion] = useState(null)
  const { setOnboarded, setRegion: saveRegion } = useAppStore()
  const navigate = useNavigate()
  const { haptic } = useTelegram()

  const finish = () => {
    if (!region) return
    saveRegion(region)
    setOnboarded()
    haptic('notification', 'success')
    navigate('/')
  }

  const dots = (
    <div className="flex gap-1.5 justify-center mb-6">
      {[0, 1, 2].map((i) => (
        <div key={i} className={`h-1 rounded-full transition-all duration-300 ${i === step ? 'w-6 bg-tg-accent' : i < step ? 'w-3 bg-tg-accent/50' : 'w-3 bg-tg-muted/20'}`} />
      ))}
    </div>
  )

  return (
    <div className="min-h-screen bg-tg-bg flex flex-col items-center justify-center p-6 max-w-app mx-auto">
      {step < 2 ? (
        <div className="text-center w-full animate-fade-in" key={step}>
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-tg-accent to-blue-600 flex items-center justify-center text-4xl mx-auto mb-6 shadow-lg shadow-tg-accent/20">
            {slides[step].emoji}
          </div>
          <h1 className="text-2xl font-bold mb-3">{slides[step].title}</h1>
          {slides[step].desc && <p className="text-sm text-tg-muted mb-8 leading-relaxed">{slides[step].desc}</p>}
          {slides[step].items && (
            <div className="space-y-3 mb-8 text-left">
              {slides[step].items.map((item, i) => (
                <div key={i} className="card flex items-center gap-3 p-4 animate-slide-left" style={{ animationDelay: `${i * 100}ms` }}>
                  <span className="text-2xl">{item.icon}</span>
                  <span className="text-sm">{item.text}</span>
                </div>
              ))}
            </div>
          )}
          {dots}
          <button onClick={() => { haptic('impact'); setStep(step + 1) }} className="btn-primary">
            Keyingi →
          </button>
        </div>
      ) : (
        <div className="w-full animate-fade-in">
          <h1 className="text-2xl font-bold text-center mb-2">📍 Viloyatingiz</h1>
          <p className="text-sm text-tg-muted text-center mb-6">Sizga yaqin e'lonlarni ko'rsatamiz</p>
          <div className="grid grid-cols-2 gap-2 mb-6">
            {REGIONS.map((r) => (
              <button
                key={r}
                onClick={() => { haptic('selection'); setRegion(r) }}
                className={`py-3 rounded-lg text-sm font-medium transition-all duration-150 ${region === r ? 'bg-tg-accent text-white shadow-lg shadow-tg-accent/20' : 'bg-tg-card text-tg-muted border border-tg-border'}`}
              >
                {r}
              </button>
            ))}
          </div>
          {dots}
          <button onClick={finish} disabled={!region} className={`btn-primary ${!region ? 'opacity-40' : ''}`}>
            Boshlash 🚀
          </button>
        </div>
      )}
    </div>
  )
}
