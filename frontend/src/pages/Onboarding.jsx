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
    desc: "O'zbekiston uchun Telegram ichida ishlaydigan mahalliy e'lonlar platformasi. Xarid qiling, soting, do'kon oching — barchasi bir joyda!",
  },
  {
    emoji: '⚡',
    title: 'Qanday ishlaydi?',
    items: [
      { icon: '📢', text: "E'lon bering va minglab xaridorlarga yeting" },
      { icon: '🏪', text: "O'z do'koningizni oching va mahsulot soting" },
      { icon: '👥', text: "Do'stlaringizni taklif qilib bonus oling" },
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

  return (
    <div className="min-h-screen bg-tg-bg flex flex-col items-center justify-center p-6 max-w-app mx-auto">
      {step < 2 ? (
        <div className="text-center w-full">
          <div className="text-6xl mb-6">{slides[step].emoji}</div>
          <h1 className="text-2xl font-bold mb-3">{slides[step].title}</h1>
          {slides[step].desc && <p className="text-sm text-tg-muted mb-8">{slides[step].desc}</p>}
          {slides[step].items && (
            <div className="space-y-4 mb-8 text-left">
              {slides[step].items.map((item, i) => (
                <div key={i} className="flex items-center gap-3 bg-tg-card rounded-xl p-4">
                  <span className="text-2xl">{item.icon}</span>
                  <span className="text-sm">{item.text}</span>
                </div>
              ))}
            </div>
          )}
          <div className="flex gap-2 justify-center mb-6">
            {[0, 1, 2].map((i) => (
              <div key={i} className={`h-1 rounded-full transition-all ${i === step ? 'w-6 bg-tg-accent' : 'w-3 bg-tg-muted/30'}`} />
            ))}
          </div>
          <button
            onClick={() => { haptic('impact'); setStep(step + 1) }}
            className="btn-primary"
          >
            Keyingi
          </button>
        </div>
      ) : (
        <div className="w-full">
          <h1 className="text-2xl font-bold text-center mb-2">📍 Viloyatingiz</h1>
          <p className="text-sm text-tg-muted text-center mb-6">Sizga yaqin e'lonlarni ko'rsatamiz</p>
          <div className="grid grid-cols-2 gap-2 mb-6">
            {REGIONS.map((r) => (
              <button
                key={r}
                onClick={() => { haptic('selection'); setRegion(r) }}
                className={`py-3 rounded-xl text-sm font-medium transition ${region === r ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}
              >
                {r}
              </button>
            ))}
          </div>
          <div className="flex gap-2 justify-center mb-4">
            {[0, 1, 2].map((i) => (
              <div key={i} className={`h-1 rounded-full transition-all ${i === 2 ? 'w-6 bg-tg-accent' : 'w-3 bg-tg-accent/50'}`} />
            ))}
          </div>
          <button onClick={finish} disabled={!region} className={`btn-primary ${!region ? 'opacity-50' : ''}`}>
            Boshlash 🚀
          </button>
        </div>
      )}
    </div>
  )
}
