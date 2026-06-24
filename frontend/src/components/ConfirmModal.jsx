import { useTelegram } from '../hooks/useTelegram'

export default function ConfirmModal({ open, title, message, onConfirm, onCancel }) {
  const { haptic } = useTelegram()
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-6 max-w-app mx-auto">
      <div className="absolute inset-0 bg-black/60" onClick={onCancel} />
      <div className="relative bg-tg-card rounded-2xl p-5 w-full">
        <h3 className="text-base font-semibold mb-2">{title}</h3>
        <p className="text-sm text-tg-muted mb-5">{message}</p>
        <div className="flex gap-3">
          <button onClick={() => { haptic('impact'); onCancel() }} className="btn-outline flex-1 text-sm">Bekor</button>
          <button onClick={() => { haptic('impact', 'medium'); onConfirm() }} className="btn-primary flex-1 text-sm">Tasdiqlash</button>
        </div>
      </div>
    </div>
  )
}
