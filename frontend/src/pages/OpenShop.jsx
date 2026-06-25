import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import StepIndicator from '../components/StepIndicator'
import { shopsAPI, paymentsAPI } from '../api/endpoints'
import { useUserStore } from '../store/useStore'
import { useTelegram } from '../hooks/useTelegram'

const SECTIONS = [
  { value: 'uyjoy', emoji: '🏠', label: 'Uy-joy' },
  { value: 'texnika', emoji: '📱', label: 'Texnika' },
  { value: 'avto', emoji: '🚗', label: 'Avtomobil' },
  { value: 'moto', emoji: '🏍', label: 'Moto' },
  { value: 'kiyim', emoji: '👕', label: 'Kiyim' },
]

const REGIONS = [
  "Toshkent", "Samarqand", "Buxoro", "Andijon", "Farg'ona",
  "Namangan", "Qashqadaryo", "Surxondaryo", "Sirdaryo",
  "Jizzax", "Navoiy", "Xorazm", "Qoraqalpog'iston",
]

export default function OpenShop() {
  const [step, setStep] = useState(0)
  const [form, setForm] = useState({ name: '', description: '', category: '', viloyat: '' })
  const [paymentMethod, setPaymentMethod] = useState(null)
  const [error, setError] = useState(null)
  const navigate = useNavigate()
  const { haptic } = useTelegram()
  const { token } = useUserStore()
  const isDemo = !token || token === 'demo-token'

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }))
  const next = () => { haptic('impact'); setError(null); setStep((s) => s + 1) }
  const back = () => { haptic('impact', 'light'); setError(null); setStep((s) => s - 1) }

  const shopMutation = useMutation({
    mutationFn: () => shopsAPI.create(form),
    onSuccess: (res) => {
      const shopId = res.data.id
      if (paymentMethod) {
        paymentMutation.mutate({ shop_id: shopId, method: paymentMethod })
      } else {
        haptic('notification', 'success')
        toast.success("Do'kon yaratildi! Admin tasdiqlashini kuting.")
        navigate('/profile')
      }
    },
    onError: (err) => {
      const detail = err.response?.data?.detail || "Do'kon yaratishda xatolik"
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail))
      toast.error("Xatolik yuz berdi")
    },
  })

  const paymentMutation = useMutation({
    mutationFn: (data) => paymentsAPI.initiate(data),
    onSuccess: (res) => {
      haptic('notification', 'success')
      localStorage.setItem('pending_payment_id', res.data.id)
      if (res.data.payment_url) {
        window.open(res.data.payment_url, '_blank')
      }
      toast.success("To'lov sahifasiga yo'naltirildi")
      navigate(`/payment-result?payment_id=${res.data.id}`)
    },
    onError: (err) => {
      const detail = err.response?.data?.detail || "To'lov xatoligi"
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail))
      toast.error("To'lov xatoligi")
    },
  })

  const isPending = shopMutation.isPending || paymentMutation.isPending

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">Do'kon ma'lumotlari</h2>
            <input placeholder="Do'kon nomi" value={form.name} onChange={(e) => set('name', e.target.value)} className="input-field mb-3" />
            <textarea placeholder="Tavsif (kamida 10 belgi)" rows={3} value={form.description}
              onChange={(e) => set('description', e.target.value)} className="input-field mb-2 resize-none" />
            <p className="text-[11px] text-tg-muted mb-4">{form.description.length}/10 belgi</p>
            <button onClick={next} disabled={form.name.length < 2 || form.description.length < 10}
              className={`btn-primary ${form.name.length < 2 || form.description.length < 10 ? 'opacity-50' : ''}`}>
              Keyingi
            </button>
          </div>
        )

      case 1:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">Kategoriya</h2>
            <div className="space-y-2">
              {SECTIONS.map((s) => (
                <button key={s.value} onClick={() => { set('category', s.value); next() }}
                  className={`w-full flex items-center gap-3 rounded-xl p-4 transition active:scale-[0.98] ${form.category === s.value ? 'bg-tg-accent text-white' : 'bg-tg-card'}`}>
                  <span className="text-2xl">{s.emoji}</span>
                  <span className="font-medium">{s.label}</span>
                </button>
              ))}
            </div>
            <button onClick={back} className="mt-4 text-xs text-tg-muted">← Orqaga</button>
          </div>
        )

      case 2:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">📍 Viloyat</h2>
            <div className="grid grid-cols-2 gap-2">
              {REGIONS.map((r) => (
                <button key={r} onClick={() => { set('viloyat', r); next() }}
                  className={`py-3 rounded-xl text-sm font-medium transition ${form.viloyat === r ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}>
                  {r}
                </button>
              ))}
            </div>
            <button onClick={back} className="mt-4 text-xs text-tg-muted">← Orqaga</button>
          </div>
        )

      case 3:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">💳 To'lov</h2>

            <div className="bg-tg-card rounded-2xl p-5 mb-4">
              <p className="text-xs text-tg-muted mb-1">Oylik obuna narxi</p>
              <p className="text-xl font-bold text-tg-accent">100 000 so'm</p>
              <p className="text-[11px] text-tg-muted mt-1">30 kunlik obuna</p>
            </div>

            <div className="bg-tg-card rounded-2xl p-4 mb-4">
              <p className="text-xs text-tg-muted mb-3">Sizning do'koningiz:</p>
              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between"><span className="text-tg-muted">Nomi</span><span>{form.name}</span></div>
                <div className="flex justify-between"><span className="text-tg-muted">Kategoriya</span><span>{SECTIONS.find(s => s.value === form.category)?.label}</span></div>
                <div className="flex justify-between"><span className="text-tg-muted">Viloyat</span><span>📍 {form.viloyat}</span></div>
              </div>
            </div>

            <p className="text-xs text-tg-muted mb-3">To'lov usulini tanlang:</p>
            <div className="space-y-2 mb-6">
              {[['payme', '💳 Payme'], ['click', '💳 Click']].map(([v, l]) => (
                <button key={v} onClick={() => { haptic('selection'); setPaymentMethod(v) }}
                  className={`w-full py-4 rounded-xl text-sm font-medium transition ${paymentMethod === v ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}>
                  {l}
                </button>
              ))}
            </div>

            {error && (
              <div className="bg-tg-red/10 border border-tg-red/20 rounded-xl p-3 mb-4">
                <p className="text-xs text-tg-red">{error}</p>
              </div>
            )}

            <button onClick={() => { setError(null); shopMutation.mutate() }}
              disabled={!paymentMethod || isPending}
              className={`btn-primary ${!paymentMethod || isPending ? 'opacity-50' : ''}`}>
              {isPending ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin">⏳</span> {shopMutation.isPending ? "Do'kon yaratilmoqda..." : "To'lov boshlanmoqda..."}
                </span>
              ) : "Do'kon ochish va to'lash"}
            </button>
            <button onClick={back} disabled={isPending} className="mt-3 text-xs text-tg-muted block mx-auto">← Orqaga</button>
          </div>
        )
    }
  }

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <h1 className="text-xl font-bold mb-4">🏪 Do'kon ochish</h1>

      {isDemo && (
        <div className="bg-tg-yellow/10 border border-tg-yellow/20 rounded-xl p-3 mb-4">
          <p className="text-xs text-tg-yellow">
            Do'kon ochish uchun Telegram orqali kiring
          </p>
        </div>
      )}

      <StepIndicator current={step} total={4} />
      {renderStep()}
    </div>
  )
}
