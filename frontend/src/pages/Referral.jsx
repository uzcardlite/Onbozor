import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { referralAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'

function formatPrice(n) {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

export default function Referral() {
  const { haptic, tg } = useTelegram()

  const { data, isLoading } = useQuery({
    queryKey: ['referral'],
    queryFn: () => referralAPI.stats().then((r) => r.data),
  })

  const copy = () => {
    if (!data) return
    navigator.clipboard.writeText(data.ref_link)
    haptic('notification', 'success')
    toast.success('Havola nusxalandi!')
  }

  const share = () => {
    if (!data) return
    haptic('impact', 'medium')
    const text = `OnBozor — O'zbekiston bozori! Ro'yxatdan o'ting va bonus oling:\n${data.ref_link}`
    const url = `https://t.me/share/url?url=${encodeURIComponent(data.ref_link)}&text=${encodeURIComponent(text)}`
    tg.openTelegramLink(url)
  }

  if (isLoading) {
    return (
      <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
        <h1 className="text-xl font-bold mb-6">👥 Referral</h1>
        <div className="space-y-4 animate-pulse">
          <div className="bg-tg-card rounded-xl h-28" />
          <div className="bg-tg-card rounded-xl h-20" />
        </div>
      </div>
    )
  }

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <h1 className="text-xl font-bold mb-6">👥 Referral</h1>

      <div className="bg-tg-card rounded-2xl p-5 mb-4">
        <p className="text-xs text-tg-muted mb-2">Sizning kodingiz</p>
        <div className="flex items-center gap-3">
          <p className="text-lg font-bold text-tg-accent flex-1 font-mono">{data?.ref_code}</p>
          <button onClick={copy} className="px-4 py-2 bg-tg-accent/10 text-tg-accent rounded-lg text-xs font-medium transition active:scale-95">
            📋 Nusxalash
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-6">
        <div className="bg-tg-card rounded-2xl p-4 text-center">
          <p className="text-2xl font-bold text-tg-accent">{data?.ref_count || 0}</p>
          <p className="text-xs text-tg-muted mt-1">Taklif qilganlar</p>
        </div>
        <div className="bg-tg-card rounded-2xl p-4 text-center">
          <p className="text-2xl font-bold text-tg-green">{formatPrice(data?.ref_earnings || 0)}</p>
          <p className="text-xs text-tg-muted mt-1">Daromad (so'm)</p>
        </div>
      </div>

      <div className="bg-tg-card rounded-2xl p-5 mb-6">
        <h3 className="text-sm font-semibold mb-2">Qanday ishlaydi?</h3>
        <div className="space-y-3 text-xs text-tg-muted">
          <div className="flex gap-3 items-start">
            <span className="text-lg">1️⃣</span>
            <p>Havolangizni do'stlaringizga yuboring</p>
          </div>
          <div className="flex gap-3 items-start">
            <span className="text-lg">2️⃣</span>
            <p>Do'stingiz ro'yxatdan o'tadi</p>
          </div>
          <div className="flex gap-3 items-start">
            <span className="text-lg">3️⃣</span>
            <p>Ularning har bir xarididan 5% bonus olasiz!</p>
          </div>
        </div>
      </div>

      <button onClick={share} className="btn-primary">
        📤 Do'stga yuborish
      </button>
    </div>
  )
}
