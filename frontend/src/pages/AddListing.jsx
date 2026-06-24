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
    const urls = []
    const prevs = []
    for (const file of files.slice(0, 5)) {
      prevs.push(URL.createObjectURL(file))
      try {
        const res = await uploadAPI.image(file)
        urls.push(res.data.url)
      } catch { toast.error("Rasm yuklashda xatolik") }
    }
    setPreviews((p) => [...p, ...prevs])
    set('image_urls', [...form.image_urls, ...urls])
    setUploading(false)
  }

  const mutation = useMutation({
    mutationFn: (data) => listingsAPI.create(data),
    onSuccess: () => {
      haptic('notification', 'success')
      toast.success("E'lon yuborildi! Admin tasdiqlashini kuting.")
      navigate('/')
    },
    onError: () => toast.error("Xatolik yuz berdi"),
  })

  const submit = () => {
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
      image_urls: form.image_urls,
    })
  }

  const formatPrice = (n) => n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">Bo'limni tanlang</h2>
            <div className="space-y-2">
              {SECTIONS.map((s) => (
                <button key={s.value} onClick={() => { set('section', s.value); next() }}
                  className="w-full flex items-center gap-3 bg-tg-card rounded-xl p-4 transition active:scale-[0.98]">
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
                  className="w-full bg-tg-card rounded-xl p-4 text-left transition active:scale-[0.98] font-medium">
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
                  className="w-full bg-tg-card rounded-xl p-4 text-left transition active:scale-[0.98] font-medium">
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
            <input type="number" placeholder="Narx (so'm)" value={form.price}
              onChange={(e) => set('price', e.target.value)} className="input-field mb-3" />
            <label className="flex items-center gap-2 text-sm text-tg-muted mb-4">
              <input type="checkbox" checked={form.negotiable} onChange={(e) => set('negotiable', e.target.checked)}
                className="w-4 h-4 accent-tg-accent" />
              Kelishiladi
            </label>
            <button onClick={next} disabled={!form.condition || !form.price} className={`btn-primary ${!form.condition || !form.price ? 'opacity-50' : ''}`}>Keyingi</button>
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
              onChange={(e) => set('description', e.target.value)} className="input-field mb-4 resize-none" />
            <button onClick={next} disabled={!form.seller_username || form.description.length < 10}
              className={`btn-primary ${!form.seller_username || form.description.length < 10 ? 'opacity-50' : ''}`}>Keyingi</button>
            <button onClick={back} className="mt-3 text-xs text-tg-muted block mx-auto">← Orqaga</button>
          </div>
        )

      case 6:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">📷 Rasmlar</h2>
            <div className="grid grid-cols-3 gap-2 mb-4">
              {previews.map((p, i) => (
                <div key={i} className="aspect-square rounded-xl overflow-hidden">
                  <img src={p} alt="" className="w-full h-full object-cover" />
                </div>
              ))}
              {previews.length < 5 && (
                <button onClick={() => fileRef.current?.click()}
                  className="aspect-square rounded-xl bg-tg-card flex items-center justify-center text-2xl text-tg-muted border-2 border-dashed border-tg-muted/20">
                  {uploading ? '⏳' : '+'}
                </button>
              )}
            </div>
            <input ref={fileRef} type="file" accept="image/*" multiple onChange={handleFiles} className="hidden" />
            <p className="text-xs text-tg-muted mb-4 text-center">Max 5 ta rasm (5MB gacha)</p>
            <button onClick={next} className="btn-primary">Keyingi</button>
            <button onClick={back} className="mt-3 text-xs text-tg-muted block mx-auto">← Orqaga</button>
          </div>
        )

      case 7:
        return (
          <div>
            <h2 className="text-lg font-semibold mb-4">📋 Tasdiqlash</h2>
            <div className="bg-tg-card rounded-xl p-4 space-y-2 text-sm mb-6">
              <p>📁 <span className="text-tg-muted">Bo'lim:</span> {form.section}</p>
              <p>📂 <span className="text-tg-muted">Kategoriya:</span> {form.category}</p>
              <p>💰 <span className="text-tg-muted">To'lov:</span> {form.payment_type}</p>
              <p>📦 <span className="text-tg-muted">Holat:</span> {form.condition}</p>
              <p>💵 <span className="text-tg-muted">Narx:</span> {formatPrice(form.price)} so'm{form.negotiable ? ' (kelishiladi)' : ''}</p>
              <p>📍 <span className="text-tg-muted">Viloyat:</span> {form.viloyat}</p>
              <p>📱 <span className="text-tg-muted">Kontakt:</span> {form.seller_username}</p>
              <p>📝 <span className="text-tg-muted">Tavsif:</span> {form.description}</p>
              <p>📷 <span className="text-tg-muted">Rasmlar:</span> {form.image_urls.length} ta</p>
            </div>
            <button onClick={submit} disabled={mutation.isPending}
              className={`btn-primary ${mutation.isPending ? 'opacity-50' : ''}`}>
              {mutation.isPending ? "Yuborilmoqda..." : "✅ Yuborish"}
            </button>
            <button onClick={back} className="mt-3 text-xs text-tg-muted block mx-auto">← Orqaga</button>
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
