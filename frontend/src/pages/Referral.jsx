import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { referralAPI } from '../api/endpoints'
import { useUserStore } from '../store/useStore'
import { useTelegram } from '../hooks/useTelegram'

function formatPrice(n) {
  return (n || 0).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

const BOT_USERNAME = import.meta.env.VITE_BOT_USERNAME || 'OnBozorBot'

export default function Referral() {
  const { haptic, tg, isTelegram } = useTelegram()
  const { user, token } = useUserStore()
  const isDemo = !token || token === 'demo-token'

  const { data, isLoading, isError } = useQuery({
    queryKey: ['referral'],
    queryFn: () => referralAPI.stats().then((r) => r.data),
    enabled: !isDemo,
    retry: false,
  })

  const refCode = data?.ref_code || user?.ref_code || 'demo123'
  const refLink = data?.ref_link || `https://t.me/${BOT_USERNAME}?start=${refCode}`
  const refCount = data?.ref_count ?? user?.ref_count ?? 0
  const refEarnings = data?.ref_earnings ?? user?.ref_earnings ?? 0

  const copy = () => {
    navigator.clipboard.writeText(refLink).then(() => {
      haptic('notification', 'success')
      toast.success('Havola nusxalandi!')
    }).catch(() => {
      toast.error('Nusxalab bo\'lmadi')
    })
  }

  const share = () => {
    haptic('impact', 'medium')
    const text = `OnBozor — O'zbekiston bozori! Ro'yxatdan o'ting va bonus oling:`
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(refLink)}&text=${encodeURIComponent(text)}`

    if (isTelegram && tg) {
      tg.openTelegramLink(shareUrl)
    } else {
      window.open(shareUrl, '_blank')
    }
  }

  if (isLoading) {
    return (
      <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
        <h1 className="text-xl font-bold mb-6">👥 Referral</h1>
        <div className="space-y-4 animate-pulse">
          <div className="bg-tg-card rounded-2xl h-28" />
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-tg-card rounded-2xl h-24" />
            <div className="bg-tg-card rounded-2xl h-24" />
          </div>
          <div className="bg-tg-card rounded-2xl h-40" />
        </div>
      </div>
    )
  }

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <h1 className="text-xl font-bold mb-6">👥 Referral</h1>

      <div className="bg-tg-card rounded-2xl p-5 mb-4">
        <p className="text-xs text-tg-muted mb-2">Sizning kodingiz</p>
        <div className="flex items-center gap-3 mb-3">
          <p className="text-lg font-bold text-tg-accent flex-1 font-mono tracking-wider">{refCode}</p>
          <button onClick={copy} className="px-4 py-2 bg-tg-accent/10 text-tg-accent rounded-lg text-xs font-medium transition active:scale-95">
            📋 Nusxalash
          </button>
        </div>
        <div className="bg-tg-bg rounded-lg p-3">
          <p className="text-[11px] text-tg-muted break-all">{refLink}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-6">
        <div className="bg-tg-card rounded-2xl p-4 text-center">
          <p className="text-2xl font-bold text-tg-accent">{refCount}</p>
          <p className="text-xs text-tg-muted mt-1">Taklif qilganlar</p>
        </div>
        <div className="bg-tg-card rounded-2xl p-4 text-center">
          <p className="text-2xl font-bold text-tg-green">{formatPrice(refEarnings)}</p>
          <p className="text-xs text-tg-muted mt-1">Daromad (so'm)</p>
        </div>
      </div>

      {refCount === 0 && (
        <div className="text-center py-6 mb-4">
          <p className="text-3xl mb-2">👥</p>
          <p className="text-sm text-tg-muted">Hali hech kim taklif qilinmagan</p>
          <p className="text-xs text-tg-muted mt-1">Havolangizni do'stlaringizga yuboring!</p>
        </div>
      )}

      <div className="bg-tg-card rounded-2xl p-5 mb-6">
        <h3 className="text-sm font-semibold mb-3">Qanday ishlaydi?</h3>
        <div className="space-y-3">
          <div className="flex gap-3 items-center">
            <div className="w-8 h-8 rounded-full bg-tg-accent/10 flex items-center justify-center text-sm shrink-0">1</div>
            <p className="text-xs text-tg-muted">Havolangizni do'stlaringizga yuboring</p>
          </div>
          <div className="flex gap-3 items-center">
            <div className="w-8 h-8 rounded-full bg-tg-accent/10 flex items-center justify-center text-sm shrink-0">2</div>
            <p className="text-xs text-tg-muted">Do'stingiz ro'yxatdan o'tadi</p>
          </div>
          <div className="flex gap-3 items-center">
            <div className="w-8 h-8 rounded-full bg-tg-accent/10 flex items-center justify-center text-sm shrink-0">3</div>
            <p className="text-xs text-tg-muted">Ularning har bir xarididan <span className="text-tg-green font-medium">5% bonus</span> olasiz!</p>
          </div>
        </div>
      </div>

      <button onClick={share} className="btn-primary">
        📤 Do'stga yuborish
      </button>

      {isDemo && (
        <p className="text-[10px] text-tg-muted text-center mt-3">
          Telegram orqali kiring — haqiqiy referral kod oling
        </p>
      )}
    </div>
  )
}
