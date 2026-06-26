import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-tg-bg flex items-center justify-center px-6 max-w-app mx-auto">
      <div className="text-center">
        <p className="text-6xl mb-4">🔍</p>
        <h1 className="text-2xl font-bold mb-2">Sahifa topilmadi</h1>
        <p className="text-sm text-tg-muted mb-6">Bu sahifa mavjud emas yoki o'chirilgan</p>
        <Link to="/" className="btn-primary inline-block">🏠 Bosh sahifaga</Link>
      </div>
    </div>
  )
}
