import { useState, useRef, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { messagesAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'

function formatPrice(n) {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

export default function Chat() {
  const { id } = useParams()
  const [text, setText] = useState('')
  const bottomRef = useRef(null)
  const { haptic } = useTelegram()
  const qc = useQueryClient()

  const { data } = useQuery({
    queryKey: ['chat', id],
    queryFn: () => messagesAPI.messages(id).then((r) => r.data),
    refetchInterval: 5000,
  })

  const sendMut = useMutation({
    mutationFn: () => messagesAPI.send(id, text),
    onSuccess: () => {
      setText('')
      haptic('impact', 'light')
      qc.invalidateQueries({ queryKey: ['chat', id] })
      qc.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [data?.messages?.length])

  const listing = data?.listing
  const messages = data?.messages || []

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!text.trim() || sendMut.isPending) return
    sendMut.mutate()
  }

  return (
    <div className="flex flex-col h-screen max-w-app mx-auto bg-tg-bg">
      {listing && (
        <Link to={`/listing/${listing.id}`} className="bg-tg-header p-3 flex items-center gap-3 shrink-0 border-b border-tg-border/30">
          <div className="w-10 h-10 rounded-lg bg-tg-card overflow-hidden shrink-0">
            {listing.image ? (
              <img src={listing.image} alt="" className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-tg-muted">📷</div>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium truncate">{listing.title}</p>
            <p className="text-xs text-tg-green font-bold">{formatPrice(listing.price)} so'm</p>
          </div>
        </Link>
      )}

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.is_mine ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[75%] rounded-2xl px-3.5 py-2 ${msg.is_mine ? 'bg-tg-accent text-white rounded-br-md' : 'bg-tg-card text-white rounded-bl-md'}`}>
              <p className="text-sm break-words">{msg.text}</p>
              <div className={`flex items-center gap-1 mt-0.5 ${msg.is_mine ? 'justify-end' : ''}`}>
                <span className="text-[9px] opacity-60">
                  {new Date(msg.created_at).toLocaleTimeString('uz', { hour: '2-digit', minute: '2-digit' })}
                </span>
                {msg.is_mine && (
                  <span className="text-[9px] opacity-60">{msg.is_read ? '✓✓' : '✓'}</span>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="shrink-0 p-3 bg-tg-header border-t border-tg-border/30">
        <div className="flex gap-2">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Xabar yozing..."
            className="flex-1 bg-tg-card border border-tg-border rounded-xl px-4 py-2.5 text-sm text-white placeholder-tg-muted focus:border-tg-accent transition-colors"
            autoFocus
          />
          <button
            type="submit"
            disabled={!text.trim() || sendMut.isPending}
            className="w-11 h-11 bg-tg-accent rounded-xl flex items-center justify-center text-white shrink-0 active:scale-95 transition-transform disabled:opacity-40"
          >
            {sendMut.isPending ? '⏳' : '➤'}
          </button>
        </div>
      </form>
    </div>
  )
}
