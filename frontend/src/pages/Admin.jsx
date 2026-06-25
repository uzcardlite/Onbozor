import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { adminAPI } from '../api/endpoints'
import { useUserStore } from '../store/useStore'
import { useTelegram } from '../hooks/useTelegram'

function formatNum(n) {
  return (n || 0).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

// ────────────── Stats Tab ──────────────

function StatsTab() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminAPI.stats().then((r) => r.data),
  })

  if (isLoading) return <SkeletonGrid />

  const cards = [
    { label: 'Foydalanuvchilar', value: data?.total_users, icon: '👥' },
    { label: "Jami e'lonlar", value: data?.total_listings, icon: '📢' },
    { label: "Faol e'lonlar", value: data?.active_listings, icon: '✅' },
    { label: 'Kutayotgan', value: data?.pending_listings, icon: '⏳' },
    { label: "Do'konlar", value: data?.total_shops, icon: '🏪' },
    { label: "Faol do'konlar", value: data?.active_shops, icon: '🟢' },
    { label: "To'lovlar", value: data?.total_payments, icon: '💳' },
    { label: 'Daromad', value: `${formatNum(data?.total_revenue)} so'm`, icon: '💰' },
  ]

  return (
    <div className="grid grid-cols-2 gap-3">
      {cards.map((c) => (
        <div key={c.label} className="bg-tg-card rounded-2xl p-4">
          <p className="text-lg mb-1">{c.icon}</p>
          <p className="text-xl font-bold">{typeof c.value === 'number' ? formatNum(c.value) : c.value}</p>
          <p className="text-[11px] text-tg-muted mt-1">{c.label}</p>
        </div>
      ))}
    </div>
  )
}

// ────────────── Users Tab ──────────────

function UsersTab() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const qc = useQueryClient()
  const { haptic } = useTelegram()

  const { data, isLoading } = useQuery({
    queryKey: ['admin-users', search, page],
    queryFn: () => adminAPI.users({ search, page, limit: 20 }).then((r) => r.data),
  })

  const blockMutation = useMutation({
    mutationFn: ({ id, blocked }) => blocked ? adminAPI.unblockUser(id) : adminAPI.blockUser(id),
    onSuccess: () => { haptic('notification', 'success'); toast.success('Yangilandi'); qc.invalidateQueries({ queryKey: ['admin-users'] }) },
  })

  const users = Array.isArray(data) ? data : data?.items || []

  return (
    <div>
      <input
        placeholder="Qidirish (ism, username)..."
        value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(1) }}
        className="input-field mb-4 text-sm"
      />

      {isLoading ? <SkeletonList /> : users.length ? (
        <div className="space-y-2">
          {users.map((u) => (
            <div key={u.id} className="bg-tg-card rounded-xl p-3 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-tg-accent/20 flex items-center justify-center text-sm font-bold text-tg-accent shrink-0">
                {u.full_name?.charAt(0) || '?'}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate">{u.full_name}</p>
                <p className="text-[11px] text-tg-muted">@{u.username || 'no_username'} · {u.viloyat || '—'}</p>
              </div>
              <button
                onClick={() => { haptic('impact'); blockMutation.mutate({ id: u.id, blocked: u.is_blocked }) }}
                className={`text-[10px] font-medium px-3 py-1.5 rounded-lg shrink-0 ${u.is_blocked ? 'bg-tg-green/20 text-tg-green' : 'bg-tg-red/20 text-tg-red'}`}
              >
                {u.is_blocked ? 'Unblock' : 'Block'}
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-tg-muted text-center py-8">Foydalanuvchilar topilmadi</p>
      )}

      {users.length >= 20 && (
        <div className="flex justify-center gap-3 mt-4">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="text-xs text-tg-accent disabled:text-tg-muted">← Oldingi</button>
          <span className="text-xs text-tg-muted">{page}-sahifa</span>
          <button onClick={() => setPage((p) => p + 1)} className="text-xs text-tg-accent">Keyingi →</button>
        </div>
      )}
    </div>
  )
}

// ────────────── Listings Tab ──────────────

function ListingsTab() {
  const [status, setStatus] = useState('pending')
  const [rejectId, setRejectId] = useState(null)
  const [reason, setReason] = useState('')
  const qc = useQueryClient()
  const { haptic } = useTelegram()

  const { data, isLoading } = useQuery({
    queryKey: ['admin-listings', status],
    queryFn: () => adminAPI.listings({ status }).then((r) => r.data),
  })

  const approveMut = useMutation({
    mutationFn: (id) => adminAPI.approveListing(id),
    onSuccess: () => { haptic('notification', 'success'); toast.success('Tasdiqlandi'); qc.invalidateQueries({ queryKey: ['admin-listings'] }); qc.invalidateQueries({ queryKey: ['admin-stats'] }) },
  })

  const rejectMut = useMutation({
    mutationFn: ({ id, reason }) => adminAPI.rejectListing(id, reason),
    onSuccess: () => { haptic('notification', 'success'); toast.success('Rad etildi'); setRejectId(null); setReason(''); qc.invalidateQueries({ queryKey: ['admin-listings'] }); qc.invalidateQueries({ queryKey: ['admin-stats'] }) },
  })

  const listings = Array.isArray(data) ? data : data?.items || []

  return (
    <div>
      <div className="flex gap-2 mb-4">
        {['pending', 'active', 'rejected'].map((s) => (
          <button
            key={s}
            onClick={() => { haptic('selection'); setStatus(s) }}
            className={`flex-1 py-2 rounded-xl text-xs font-medium transition ${status === s ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}
          >
            {s === 'pending' ? '⏳ Kutayotgan' : s === 'active' ? '✅ Faol' : '❌ Rad'}
          </button>
        ))}
      </div>

      {isLoading ? <SkeletonList /> : listings.length ? (
        <div className="space-y-3">
          {listings.map((l) => (
            <div key={l.id} className="bg-tg-card rounded-xl p-4">
              <div className="flex gap-3 mb-3">
                <div className="w-16 h-16 rounded-lg bg-tg-bg overflow-hidden shrink-0">
                  {l.image_urls?.[0] ? (
                    <img src={l.image_urls[0]} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-tg-muted">📷</div>
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{l.category}{l.subcategory ? ` → ${l.subcategory}` : ''}</p>
                  <p className="text-sm font-bold text-tg-accent">{formatNum(l.price)} so'm</p>
                  <p className="text-[11px] text-tg-muted">📍 {l.viloyat} · {l.seller_username}</p>
                </div>
              </div>
              <p className="text-xs text-tg-muted mb-3 line-clamp-2">{l.description}</p>

              {l.reject_reason && (
                <p className="text-xs text-tg-red mb-3">Sabab: {l.reject_reason}</p>
              )}

              {status === 'pending' && (
                rejectId === l.id ? (
                  <div className="space-y-2">
                    <input placeholder="Rad etish sababi..." value={reason} onChange={(e) => setReason(e.target.value)} className="input-field text-xs" />
                    <div className="flex gap-2">
                      <button onClick={() => setRejectId(null)} className="btn-outline flex-1 text-xs !py-2">Bekor</button>
                      <button
                        onClick={() => { if (reason.trim()) rejectMut.mutate({ id: l.id, reason }) }}
                        disabled={!reason.trim()}
                        className={`btn-primary flex-1 text-xs !py-2 !bg-tg-red ${!reason.trim() ? 'opacity-50' : ''}`}
                      >
                        Rad etish
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <button
                      onClick={() => { haptic('impact', 'medium'); approveMut.mutate(l.id) }}
                      className="btn-primary flex-1 text-xs !py-2"
                    >
                      ✅ Tasdiqlash
                    </button>
                    <button
                      onClick={() => { haptic('impact'); setRejectId(l.id); setReason('') }}
                      className="btn-outline flex-1 text-xs !py-2 !border-tg-red !text-tg-red"
                    >
                      ❌ Rad etish
                    </button>
                  </div>
                )
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-tg-muted text-center py-8">
          {status === 'pending' ? "Kutayotgan e'lonlar yo'q" : "E'lonlar yo'q"}
        </p>
      )}
    </div>
  )
}

// ────────────── Shops Tab ──────────────

function ShopsTab() {
  const [status, setStatus] = useState('pending')
  const qc = useQueryClient()
  const { haptic } = useTelegram()

  const { data, isLoading } = useQuery({
    queryKey: ['admin-shops', status],
    queryFn: () => adminAPI.shops({ status }).then((r) => r.data),
  })

  const approveMut = useMutation({
    mutationFn: (id) => adminAPI.approveShop(id),
    onSuccess: () => { haptic('notification', 'success'); toast.success('Tasdiqlandi'); qc.invalidateQueries({ queryKey: ['admin-shops'] }) },
  })

  const rejectMut = useMutation({
    mutationFn: (id) => adminAPI.rejectShop(id),
    onSuccess: () => { haptic('notification', 'success'); toast.success('Rad etildi'); qc.invalidateQueries({ queryKey: ['admin-shops'] }) },
  })

  const shops = Array.isArray(data) ? data : data?.items || []

  return (
    <div>
      <div className="flex gap-2 mb-4">
        {['pending', 'active', 'rejected'].map((s) => (
          <button
            key={s}
            onClick={() => { haptic('selection'); setStatus(s) }}
            className={`flex-1 py-2 rounded-xl text-xs font-medium transition ${status === s ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}
          >
            {s === 'pending' ? '⏳ Kutayotgan' : s === 'active' ? '✅ Faol' : '❌ Rad'}
          </button>
        ))}
      </div>

      {isLoading ? <SkeletonList /> : shops.length ? (
        <div className="space-y-3">
          {shops.map((s) => (
            <div key={s.id} className="bg-tg-card rounded-xl p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-12 h-12 rounded-xl bg-tg-bg flex items-center justify-center text-xl shrink-0">
                  {s.icon_url ? <img src={s.icon_url} alt="" className="w-full h-full object-cover rounded-xl" /> : '🏪'}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">{s.name}</p>
                  <p className="text-[11px] text-tg-muted">📍 {s.viloyat || '—'} · {s.category}</p>
                </div>
              </div>
              <p className="text-xs text-tg-muted mb-3 line-clamp-2">{s.description}</p>

              {status === 'pending' && (
                <div className="flex gap-2">
                  <button onClick={() => { haptic('impact', 'medium'); approveMut.mutate(s.id) }} className="btn-primary flex-1 text-xs !py-2">✅ Tasdiqlash</button>
                  <button onClick={() => { haptic('impact'); rejectMut.mutate(s.id) }} className="btn-outline flex-1 text-xs !py-2 !border-tg-red !text-tg-red">❌ Rad etish</button>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-tg-muted text-center py-8">Do'konlar yo'q</p>
      )}
    </div>
  )
}

// ────────────── Broadcast Tab ──────────────

function BroadcastTab() {
  const [text, setText] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const { haptic } = useTelegram()

  const mutation = useMutation({
    mutationFn: () => adminAPI.broadcast({ text, image_url: imageUrl || null }),
    onSuccess: (res) => {
      haptic('notification', 'success')
      toast.success(`${res.data?.sent_count || 0} foydalanuvchiga yuborildi`)
      setText('')
      setImageUrl('')
    },
    onError: () => toast.error('Xatolik yuz berdi'),
  })

  return (
    <div>
      <textarea
        placeholder="Xabar matni..."
        rows={5}
        value={text}
        onChange={(e) => setText(e.target.value)}
        className="input-field mb-3 resize-none text-sm"
      />
      <input
        placeholder="Rasm URL (ixtiyoriy)"
        value={imageUrl}
        onChange={(e) => setImageUrl(e.target.value)}
        className="input-field mb-4 text-sm"
      />
      <button
        onClick={() => mutation.mutate()}
        disabled={!text.trim() || mutation.isPending}
        className={`btn-primary ${!text.trim() || mutation.isPending ? 'opacity-50' : ''}`}
      >
        {mutation.isPending ? 'Yuborilmoqda...' : '📨 Broadcast yuborish'}
      </button>
    </div>
  )
}

// ────────────── Skeletons ──────────────

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-2 gap-3">
      {Array.from({ length: 6 }, (_, i) => <div key={i} className="bg-tg-card rounded-2xl h-24 animate-pulse" />)}
    </div>
  )
}

function SkeletonList() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }, (_, i) => <div key={i} className="bg-tg-card rounded-xl h-20 animate-pulse" />)}
    </div>
  )
}

// ────────────── Main Admin Page ──────────────

const TABS = [
  { key: 'stats', label: '📊', title: 'Statistika' },
  { key: 'users', label: '👥', title: 'Userlar' },
  { key: 'listings', label: '📢', title: "E'lonlar" },
  { key: 'shops', label: '🏪', title: "Do'konlar" },
  { key: 'broadcast', label: '📨', title: 'Broadcast' },
]

export default function Admin() {
  const [tab, setTab] = useState('stats')
  const { user } = useUserStore()
  const { haptic } = useTelegram()

  if (!user?.is_admin) {
    return (
      <div className="min-h-screen bg-tg-bg flex items-center justify-center max-w-app mx-auto px-4">
        <div className="text-center">
          <p className="text-5xl mb-4">🔒</p>
          <h1 className="text-lg font-bold mb-2">Ruxsat yo'q</h1>
          <p className="text-sm text-tg-muted">Admin paneliga faqat adminlar kira oladi.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <h1 className="text-xl font-bold mb-4">🔧 Admin Panel</h1>

      <div className="flex gap-1 bg-tg-card rounded-xl p-1 mb-5">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => { haptic('selection'); setTab(t.key) }}
            className={`flex-1 py-2 rounded-lg text-center transition ${tab === t.key ? 'bg-tg-accent text-white' : 'text-tg-muted'}`}
          >
            <span className="text-sm block">{t.label}</span>
            <span className="text-[9px] block mt-0.5">{t.title}</span>
          </button>
        ))}
      </div>

      {tab === 'stats' && <StatsTab />}
      {tab === 'users' && <UsersTab />}
      {tab === 'listings' && <ListingsTab />}
      {tab === 'shops' && <ShopsTab />}
      {tab === 'broadcast' && <BroadcastTab />}
    </div>
  )
}
