import { useQuery } from '@tanstack/react-query'
import { gamificationAPI } from '../api/endpoints'
import { useUserStore } from '../store/useStore'
import { useTelegram } from '../hooks/useTelegram'

const LEVEL_NAMES = { 1: 'Yangi', 2: 'Faol', 3: 'Tajribali', 4: 'Professional', 5: 'Ekspert ⭐' }
const MEDAL = ['🥇', '🥈', '🥉']

export default function Leaderboard() {
  const { user, token } = useUserStore()
  const { haptic } = useTelegram()
  const isDemo = !token || token === 'demo-token'

  const { data: leaders, isLoading } = useQuery({
    queryKey: ['leaderboard'],
    queryFn: () => gamificationAPI.leaderboard().then((r) => r.data),
  })

  const { data: myStats } = useQuery({
    queryKey: ['my-game-stats'],
    queryFn: () => gamificationAPI.myStats().then((r) => r.data),
    enabled: !isDemo,
    retry: false,
  })

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <h1 className="text-xl font-bold mb-2">🏆 Reyting jadvali</h1>
      <p className="text-xs text-tg-muted mb-5">Eng faol sotuvchilar</p>

      {myStats && (
        <div className="card p-4 mb-5 flex items-center justify-between">
          <div>
            <p className="text-xs text-tg-muted">Sizning o'rningiz</p>
            <p className="text-lg font-bold text-tg-accent">#{myStats.rank}</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-bold">{myStats.points} ball</p>
            <p className="text-[10px] text-tg-muted">{LEVEL_NAMES[myStats.level] || 'Yangi'}</p>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">{Array.from({ length: 10 }, (_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}</div>
      ) : leaders?.length ? (
        <div className="space-y-2">
          {leaders.map((u, i) => (
            <div key={u.id} className={`card p-3 flex items-center gap-3 ${i < 3 ? 'border border-tg-yellow/30' : ''}`}>
              <div className="w-8 text-center shrink-0">
                {i < 3 ? (
                  <span className="text-xl">{MEDAL[i]}</span>
                ) : (
                  <span className="text-sm text-tg-muted font-bold">{i + 1}</span>
                )}
              </div>
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-tg-accent to-blue-600 flex items-center justify-center text-xs font-bold text-white shrink-0">
                {u.name?.charAt(0)?.toUpperCase() || '?'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1">
                  <p className="text-sm font-medium truncate">{u.name}</p>
                  {u.is_verified && <span className="text-tg-accent text-[10px]">✓</span>}
                </div>
                <p className="text-[10px] text-tg-muted">{LEVEL_NAMES[u.level] || 'Yangi'}</p>
              </div>
              <p className="text-sm font-bold text-tg-accent shrink-0">{u.points}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-3xl mb-3">🏆</p>
          <p className="text-sm text-tg-muted">Hali reyting yo'q</p>
        </div>
      )}
    </div>
  )
}
