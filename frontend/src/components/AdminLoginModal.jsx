import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useTelegram } from '../hooks/useTelegram'

const ADMIN_LOGIN = 'admin'
const ADMIN_PASSWORD = '@dmin26'

export default function AdminLoginModal({ open, onClose }) {
  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const { haptic } = useTelegram()

  if (!open) return null

  const submit = (e) => {
    e.preventDefault()
    if (login === ADMIN_LOGIN && password === ADMIN_PASSWORD) {
      localStorage.setItem('admin_authenticated', 'true')
      haptic('notification', 'success')
      toast.success('Xush kelibsiz, admin!')
      onClose()
      navigate('/admin')
    } else {
      haptic('notification', 'error')
      toast.error("Login yoki parol noto'g'ri")
    }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center px-6 max-w-app mx-auto">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <form onSubmit={submit} className="relative bg-tg-card rounded-2xl p-5 w-full animate-slide-up">
        <div className="text-center mb-4">
          <p className="text-3xl mb-2">🔐</p>
          <h3 className="text-lg font-bold">Admin kirish</h3>
        </div>
        <input
          value={login}
          onChange={(e) => setLogin(e.target.value)}
          placeholder="Login"
          autoFocus
          className="input-field mb-3"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Parol"
          className="input-field mb-4"
        />
        <div className="flex gap-2">
          <button type="button" onClick={onClose} className="btn-outline flex-1 text-sm">Bekor</button>
          <button type="submit" className="btn-primary flex-1 text-sm">Kirish</button>
        </div>
      </form>
    </div>
  )
}
