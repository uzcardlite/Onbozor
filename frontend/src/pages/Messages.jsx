import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { messagesAPI } from '../api/endpoints'
import { useUserStore } from '../store/useStore'
import { ShopSkeleton } from '../components/LoadingSkeleton'

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000
  if (diff < 60) return 'hozirgina'
  if (diff < 3600) return `${Math.floor(diff / 60)} daq`
  if (diff < 86400) return `${Math.floor(diff / 3600)} soat`
  return `${Math.floor(diff / 86400)} kun`
}

export default function Messages() {
  const { token } = useUserStore()
  const isDemo = !token || token === 'demo-token'

  const { data: conversations, isLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => messagesAPI.conversations().then((r) => r.data),
    enabled: !isDemo,
    refetchInterval: 10000,
    retry: false,
  })

  if (isDemo) {
    return (
      <div className="pb-20 px-4 pt-4 max-w-app mx-auto text-center py-16">
        <p className="text-3xl mb-3">💬</p>
        <p className="text-sm text-tg-muted">Telegram orqali kiring</p>
      </div>
    )
  }

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <h1 className="text-xl font-bold mb-4">💬 Xabarlar</h1>

      {isLoading ? (
        <div className="space-y-3">{Array.from({ length: 5 }, (_, i) => <ShopSkeleton key={i} />)}</div>
      ) : conversations?.length ? (
        <div className="space-y-2">
          {conversations.map((c) => (
            <Link
              key={c.id}
              to={`/messages/${c.id}`}
              className="card p-3 flex items-center gap-3 active:scale-[0.98] transition-transform block"
            >
              <div className="w-11 h-11 rounded-xl bg-tg-bg overflow-hidden shrink-0">
                {c.listing_image ? (
                  <img src={c.listing_image} alt="" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-lg text-tg-muted">📷</div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-center">
                  <p className="text-sm font-medium truncate">{c.other_name}</p>
                  <span className="text-[10px] text-tg-muted shrink-0">{timeAgo(c.last_message_at)}</span>
                </div>
                <p className="text-[11px] text-tg-accent truncate">{c.listing_title}</p>
                <p className="text-xs text-tg-muted truncate">{c.last_message || 'Yangi suhbat'}</p>
              </div>
              {c.unread > 0 && (
                <span className="w-5 h-5 bg-tg-accent rounded-full text-[10px] font-bold flex items-center justify-center shrink-0">{c.unread}</span>
              )}
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-3xl mb-3">💬</p>
          <p className="text-sm text-tg-muted mb-2">Hali xabarlar yo'q</p>
          <p className="text-xs text-tg-muted">E'lonlardagi "Sotuvchiga yozish" tugmasini bosing</p>
        </div>
      )}
    </div>
  )
}
