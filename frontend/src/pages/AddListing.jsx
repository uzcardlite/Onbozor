import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import StepIndicator from '../components/StepIndicator'
import { listingsAPI, uploadAPI } from '../api/endpoints'
import { useTelegram } from '../hooks/useTelegram'

const SECTIONS = [
  { value: 'uyjoy', emoji: '🏠', label: 'Uy-joy' },
  { value: 'texnika', emoji: '📱', label: 'Texnika' },
  { value: 'avto', emoji: '🚗', label: 'Avtomobil' },
  { value: 'moto', emoji: '🏍', label: 'Moto' },
  { value: 'kiyim', emoji: '👕', label: 'Kiyim' },
]

const SUBCATS = {
  uyjoy: ['Sotish', 'Ijara', 'Dacha', 'Garaj'],
  texnika: ['Telefon', 'Noutbuk', 'Maishiy texnika', 'Boshqalar'],
  avto: ['Yangi', 'Ishlatilgan', 'Ehtiyot qismlar'],
  moto: ['Skuterlar', 'Motolar'],
  kiyim: ['Erkak', 'Ayol', 'Bola'],
}

const REGIONS = [
  "Toshkent", "Samarqand", "Buxoro", "Andijon", "Farg'ona",
  "Namangan", "Qashqadaryo", "Surxondaryo", "Sirdaryo",
  "Jizzax", "Navoiy", "Xorazm", "Qoraqalpog'iston",
]

export default function AddListing() {
  const [step, setStep] = useState(0)
  const [form, setForm] = useState({
    section: '', category: '', payment_type: '', condition: '',
    price: '', viloyat: '', seller_username: '', description: '',
    negotiable: false, image_urls: [],
  })
  const [previews, setPreviews] = useState([])
  const [uploading, setUploading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState(null)
  const fileRef = useRef()
  const navigate = useNavigate()
  const { haptic } = useTelegram()

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }))
  const next = () => { haptic('impact'); setStep((s) => s + 1) }
  const back = () => { haptic('impact', 'light'); setStep((s) => s - 1) }

  const handleFiles = async (e) => {
    const files = Array.from(e.target.files)
    if (!files.length) return
    setUploading(true)
    for (const file of files.slice(0, 5 - previews.length)) {
      const localUrl = URL.createObjectURL(file)
      try {
        const res = await uploadAPI.image(file)
        setPreviews((p) => [...p, localUrl])
        setForm((f) => ({ ...f, image_urls: [...f.image_urls, res.data.url] }))
      } catch (err) {
        setPreviews((p) => [...p, localUrl])
        setForm((f) => ({ ...f, image_urls: [...f.image_urls, localUrl] }))
        toast('Rasm lokal saqlandi', { icon: '📷' })
      }
    }
    setUploading(false)
  }

  const removeImage = (index) => {
    haptic('impact', 'light')
    setPreviews((p) => p.filter((_, i) => i !== index))
    setForm((p) => ({ ...p, image_urls: p.image_urls.filter((_, i) => i !== index) }))
  }

  const mutation = useMutation({
    mutationFn: (data) => listingsAPI.create(data),
    onSuccess: () => {
      haptic('notification', 'success')
      setSubmitted(true)
    },
    onError: (err) => {
      haptic('notification', 'error')
      const detail = err.response?.data?.detail || err.response?.data?.error || "Xatolik yuz berdi"
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail))
      toast.error("E'lon yuborishda xatolik")
    },
  })

  const submit = () => {
    setError(null)
    const validUrls = form.image_urls.filter(u => u.startsWith('http') || u.startsWith('data:'))
    mutation.mutate({
      section: form.section,
      category: form.category,
      payment_type: form.payment_type,
      condition: form.condition,
      price: parseInt(form.price),
      negotiable: form.negotiable,
      viloyat: form.viloyat,
      seller_username: form.seller_username,
      description: form.description,
      image_urls: validUrls,
    })
  }

  const formatPrice = (n) => n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')

  if (submitted) {
    return (
      <div className="min-h-screen bg-tg-bg flex items-center justify-center px-6 max-w-app mx-auto">
        <div className="text-center w-full">
          <div className="text-6xl mb-4">✅</div>
          <h1 className="text-2xl font-bold mb-2">E'loningiz qabul qilindi!</h1>
          <p className="text-sm text-tg-muted mb-8">
            Admin tasdiqlashini kuting. Tasdiqlangandan keyin e'loningiz barchaga ko'rinadi.
          </p>
          <button onClick={() => navigate('/')} className="btn-primary mb-3">
            🏠 Bosh sahifaga
          </button>
          <button onClick={() => { setSubmitted(false); setStep(0); setForm({
            section: '', category: '', payment_type: '', condition: '',
            price: '', viloyat: '', seller_username: '', description: '',
            negotiable: false, image_urls: [],
          }); setPreviews([]) }} className="btn-outline">
            📢 Yana e'lon berish
          </button>
        </div>
      </div>
    )
  }

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">Bo'limni tanlang</h2>
            <div className="space-y-2">
              {SECTIONS.map((s) => (
                <button key={s.value} onClick={() => { set('section', s.value); next() }}
                  className={`w-full flex items-center gap-3 rounded-xl p-4 transition active:scale-[0.98] ${form.section === s.value ? 'bg-tg-accent text-white' : 'bg-tg-card'}`}>
                  <span className="text-2xl">{s.emoji}</span>
                  <span className="font-medium">{s.label}</span>
                </button>
              ))}
            </div>
          </div>
        )

      case 1:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">Kategoriyani tanlang</h2>
            <div className="space-y-2">
              {(SUBCATS[form.section] || []).map((c) => (
                <button key={c} onClick={() => { set('category', c); next() }}
                  className={`w-full rounded-xl p-4 text-left transition active:scale-[0.98] font-medium ${form.category === c ? 'bg-tg-accent text-white' : 'bg-tg-card'}`}>
                  {c}
                </button>
              ))}
            </div>
            <button onClick={back} className="mt-4 text-xs text-tg-muted">← Orqaga</button>
          </div>
        )

      case 2:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">To'lov turi</h2>
            <div className="space-y-2">
              {[['naqd', '💵 Naqd'], ['nasiya', '💳 Nasiya'], ['ikkalasi', '💵💳 Ikkalasi']].map(([v, l]) => (
                <button key={v} onClick={() => { set('payment_type', v); next() }}
                  className={`w-full rounded-xl p-4 text-left transition active:scale-[0.98] font-medium ${form.payment_type === v ? 'bg-tg-accent text-white' : 'bg-tg-card'}`}>
                  {l}
                </button>
              ))}
            </div>
            <button onClick={back} className="mt-4 text-xs text-tg-muted">← Orqaga</button>
          </div>
        )

      case 3:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">Holat va narx</h2>
            <div className="flex gap-2 mb-4">
              {[['yangi', '🆕 Yangi'], ['ishlatilgan', '♻️ Ishlatilgan']].map(([v, l]) => (
                <button key={v} onClick={() => { haptic('selection'); set('condition', v) }}
                  className={`flex-1 py-3 rounded-xl text-sm font-medium transition ${form.condition === v ? 'bg-tg-accent text-white' : 'bg-tg-card text-tg-muted'}`}>
                  {l}
                </button>
              ))}
            </div>
            <input type="number" inputMode="numeric" placeholder="Narx (so'm)" value={form.price}
              onChange={(e) => set('price', e.target.value)} className="input-field mb-3" />
            {form.price && <p className="text-xs text-tg-accent mb-3">{formatPrice(form.price)} so'm</p>}
            <label className="flex items-center gap-2 text-sm text-tg-muted mb-4">
              <input type="checkbox" checked={form.negotiable} onChange={(e) => set('negotiable', e.target.checked)}
                className="w-4 h-4 accent-tg-accent" />
              Kelishiladi
            </label>
            <button onClick={next} disabled={!form.condition || !form.price}
              className={`btn-primary ${!form.condition || !form.price ? 'opacity-50' : ''}`}>Keyingi</button>
            <button onClick={back} className="mt-3 text-xs text-tg-muted block mx-auto">← Orqaga</button>
          </div>
        )

      case 4:
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

      case 5:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">Kontakt va tavsif</h2>
            <input placeholder="@username" value={form.seller_username}
              onChange={(e) => set('seller_username', e.target.value)} className="input-field mb-3" />
            <textarea placeholder="E'lon tavsifi (kamida 10 belgi)" rows={4} value={form.description}
              onChange={(e) => set('description', e.target.value)} className="input-field mb-2 resize-none" />
            <p className="text-[11px] text-tg-muted mb-4">{form.description.length}/10 belgi</p>
            <button onClick={next} disabled={!form.seller_username || form.description.length < 10}
              className={`btn-primary ${!form.seller_username || form.description.length < 10 ? 'opacity-50' : ''}`}>Keyingi</button>
            <button onClick={back} className="mt-3 text-xs text-tg-muted block mx-auto">← Orqaga</button>
          </div>
        )

      case 6:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-1">📷 Rasmlar</h2>
            <p className="text-xs text-tg-muted mb-4">Ixtiyoriy — rasmsiz ham e'lon beriladi</p>
            <div className="grid grid-cols-3 gap-2 mb-4">
              {previews.map((p, i) => (
                <div key={i} className="aspect-square rounded-xl overflow-hidden relative">
                  <img src={p} alt="" className="w-full h-full object-cover" />
                  <button onClick={() => removeImage(i)}
                    className="absolute top-1 right-1 w-6 h-6 bg-black/60 rounded-full text-xs text-white flex items-center justify-center">✕</button>
                </div>
              ))}
              {previews.length < 5 && (
                <button onClick={() => fileRef.current?.click()} disabled={uploading}
                  className="aspect-square rounded-xl bg-tg-card flex items-center justify-center text-2xl text-tg-muted border-2 border-dashed border-tg-muted/20">
                  {uploading ? <span className="animate-spin">⏳</span> : '+'}
                </button>
              )}
            </div>
            <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={handleFiles} className="hidden" />
            <p className="text-xs text-tg-muted mb-4 text-center">
              {previews.length}/5 rasm · JPG, PNG, WEBP · max 30MB
            </p>
            <button onClick={next} className="btn-primary">Keyingi</button>
            <button onClick={back} className="mt-3 text-xs text-tg-muted block mx-auto">← Orqaga</button>
          </div>
        )

      case 7:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">📋 Tasdiqlash</h2>
            <div className="bg-tg-card rounded-xl p-4 space-y-2.5 text-sm mb-4">
              <div className="flex justify-between"><span className="text-tg-muted">Bo'lim</span><span>{SECTIONS.find(s => s.value === form.section)?.label}</span></div>
              <div className="flex justify-between"><span className="text-tg-muted">Kategoriya</span><span>{form.category}</span></div>
              <div className="flex justify-between"><span className="text-tg-muted">To'lov</span><span>{form.payment_type}</span></div>
              <div className="flex justify-between"><span className="text-tg-muted">Holat</span><span>{form.condition === 'yangi' ? '🆕 Yangi' : '♻️ Ishlatilgan'}</span></div>
              <div className="flex justify-between"><span className="text-tg-muted">Narx</span><span className="text-tg-accent font-bold">{formatPrice(form.price)} so'm</span></div>
              {form.negotiable && <div className="flex justify-between"><span className="text-tg-muted">Kelishiladi</span><span>✅</span></div>}
              <div className="flex justify-between"><span className="text-tg-muted">Viloyat</span><span>📍 {form.viloyat}</span></div>
              <div className="flex justify-between"><span className="text-tg-muted">Kontakt</span><span>{form.seller_username}</span></div>
              <div className="flex justify-between"><span className="text-tg-muted">Rasmlar</span><span>📷 {form.image_urls.length} ta</span></div>
            </div>
            <p className="text-xs text-tg-muted mb-2 px-1">{form.description}</p>

            {previews.length > 0 && (
              <div className="flex gap-2 overflow-x-auto pb-2 mb-4">
                {previews.map((p, i) => (
                  <img key={i} src={p} alt="" className="w-16 h-16 rounded-lg object-cover shrink-0" />
                ))}
              </div>
            )}

            {error && (
              <div className="bg-tg-red/10 border border-tg-red/20 rounded-xl p-3 mb-4">
                <p className="text-xs text-tg-red">{error}</p>
              </div>
            )}

            <button onClick={submit} disabled={mutation.isPending}
              className={`btn-primary ${mutation.isPending ? 'opacity-50' : ''}`}>
              {mutation.isPending ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin">⏳</span> Yuborilmoqda...
                </span>
              ) : "✅ Yuborish"}
            </button>
            <button onClick={back} disabled={mutation.isPending} className="mt-3 text-xs text-tg-muted block mx-auto">← Orqaga</button>
          </div>
        )
    }
  }

  return (
    <div className="pb-20 px-4 pt-4 max-w-app mx-auto">
      <h1 className="text-xl font-bold mb-4">📢 E'lon berish</h1>
      <StepIndicator current={step} total={8} />
      {renderStep()}
    </div>
  )
}
