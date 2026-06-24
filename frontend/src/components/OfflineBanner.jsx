import { useState, useEffect } from 'react'

export default function OfflineBanner() {
  const [offline, setOffline] = useState(!navigator.onLine)

  useEffect(() => {
    const on = () => setOffline(false)
    const off = () => setOffline(true)
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off) }
  }, [])

  if (!offline) return null

  return (
    <div className="fixed top-0 left-0 right-0 bg-tg-red text-white text-xs text-center py-2 z-[60] max-w-app mx-auto">
      📡 Internet aloqasi yo'q
    </div>
  )
}
