import { useState, useEffect, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useTelegram } from '../hooks/useTelegram'
import api from '../api/client'

function Confetti() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight

    const colors = ['#2AABEE', '#4ade80', '#e8b94a', '#f56565', '#a78bfa', '#fb923c']
    const pieces = Array.from({ length: 100 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height - canvas.height,
      r: Math.random() * 6 + 3,
      dx: (Math.random() - 0.5) * 4,
      dy: Math.random() * 3 + 2,
      rot: Math.random() * 360,
      drot: (Math.random() - 0.5) * 10,
      color: colors[Math.floor(Math.random() * colors.length)],
    }))

    let animId
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      pieces.forEach((p) => {
        ctx.save()
        ctx.translate(p.x, p.y)
        ctx.rotate((p.rot * Math.PI) / 180)
        ctx.fillStyle = p.color
        ctx.fillRect(-p.r, -p.r / 2, p.r * 2, p.r)
        ctx.restore()
        p.x += p.dx
        p.y += p.dy
        p.rot += p.drot
        p.dy += 0.05
        if (p.y > canvas.height + 20) {
          p.y = -10
          p.x = Math.random() * canvas.width
          p.dy = Math.random() * 3 + 2
        }
      })
      animId = requestAnimationFrame(draw)
    }
    draw()
    return () => cancelAnimationFrame(animId)
  }, [])

  return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-50" />
}

export default function PaymentResult() {
  const [params] = useSearchParams()
  const paymentId = params.get('payment_id') || localStorage.getItem('pending_payment_id')
  const [status, setStatus] = useState('polling')
  const [attempts, setAttempts] = useState(0)
  const navigate = useNavigate()
  const { haptic } = useTelegram()

  useEffect(() => {
    if (!paymentId) {
      setStatus('error')
      return
    }

    const poll = async () => {
      try {
        const res = await api.get(`/payments/status/${paymentId}`)
        const s = res.data.status

        if (s === 'paid') {
          setStatus('success')
          haptic('notification', 'success')
          localStorage.removeItem('pending_payment_id')
          return
        }
        if (s === 'failed' || s === 'cancelled') {
          setStatus('failed')
          haptic('notification', 'error')
          localStorage.removeItem('pending_payment_id')
          return
        }

        setAttempts((a) => a + 1)
        if (attempts < 30) {
          setTimeout(poll, 3000)
        } else {
          setStatus('timeout')
        }
      } catch {
        setStatus('error')
      }
    }

    const timer = setTimeout(poll, 1000)
    return () => clearTimeout(timer)
  }, [paymentId, attempts])

  return (
    <div className="min-h-screen bg-tg-bg flex items-center justify-center px-6 max-w-app mx-auto">
      {status === 'success' && <Confetti />}

      <div className="text-center w-full">
        {status === 'polling' && (
          <>
            <div className="text-5xl mb-4 animate-pulse">⏳</div>
            <h1 className="text-xl font-bold mb-2">To'lov tekshirilmoqda</h1>
            <p className="text-sm text-tg-muted">Iltimos, kuting...</p>
            <div className="mt-6 flex justify-center">
              <div className="w-8 h-8 border-2 border-tg-accent border-t-transparent rounded-full animate-spin" />
            </div>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="text-6xl mb-4">🎉</div>
            <h1 className="text-2xl font-bold mb-2 text-tg-green">Do'koningiz faollashdi!</h1>
            <p className="text-sm text-tg-muted mb-2">
              To'lov muvaffaqiyatli qabul qilindi.
            </p>
            <div className="bg-tg-card rounded-xl p-4 mb-8 text-sm">
              <div className="flex justify-between mb-2"><span className="text-tg-muted">Obuna</span><span className="text-tg-green font-medium">30 kun</span></div>
              <div className="flex justify-between"><span className="text-tg-muted">Holat</span><span className="text-tg-green font-medium">✅ Faol</span></div>
            </div>
            <button onClick={() => navigate('/profile')} className="btn-primary mb-3">
              🏪 Do'konimga o'tish
            </button>
            <button onClick={() => navigate('/add-listing')} className="btn-outline">
              📢 Mahsulot qo'shish
            </button>
          </>
        )}

        {status === 'failed' && (
          <>
            <div className="text-5xl mb-4">😔</div>
            <h1 className="text-xl font-bold mb-2 text-tg-red">To'lov amalga oshmadi</h1>
            <p className="text-sm text-tg-muted mb-8">
              Iltimos, qaytadan urinib ko'ring yoki boshqa to'lov usulini tanlang.
            </p>
            <button onClick={() => navigate('/open-shop')} className="btn-primary mb-3">
              Qaytadan urinish
            </button>
            <button onClick={() => navigate('/')} className="btn-outline">
              Bosh sahifa
            </button>
          </>
        )}

        {status === 'timeout' && (
          <>
            <div className="text-5xl mb-4">⏰</div>
            <h1 className="text-xl font-bold mb-2 text-tg-yellow">Vaqt tugadi</h1>
            <p className="text-sm text-tg-muted mb-8">
              To'lov holati aniqlanmadi. Agar to'lov amalga oshgan bo'lsa, biroz kuting.
            </p>
            <button onClick={() => { setAttempts(0); setStatus('polling') }} className="btn-primary mb-3">
              Qayta tekshirish
            </button>
            <button onClick={() => navigate('/profile')} className="btn-outline">
              Profilga o'tish
            </button>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="text-5xl mb-4">⚠️</div>
            <h1 className="text-xl font-bold mb-2 text-tg-red">Xatolik</h1>
            <p className="text-sm text-tg-muted mb-8">Nimadir xato ketdi.</p>
            <button onClick={() => navigate('/')} className="btn-primary">Bosh sahifa</button>
          </>
        )}
      </div>
    </div>
  )
}
