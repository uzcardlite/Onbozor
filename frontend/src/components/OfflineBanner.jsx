import { useState, useEffect } from 'react'

export default function OfflineBanner() {
  const [offline, setOffline] = useState(!navigator.onLine)
  const [wasOffline, setWasOffline] = useState(false)

  useEffect(() => {
    const goOnline = () => {
      setOffline(false)
      if (wasOffline) {
        setWasOffline(false)
        setTimeout(() => setWasOffline(false), 3000)
      }
    }
    const goOffline = () => { setOffline(true); setWasOffline(true) }
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => { window.removeEventListener('online', goOnline); window.removeEventListener('offline', goOffline) }
  }, [wasOffline])

  if (!offline) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-[60] max-w-app mx-auto animate-slide-up">
      <div className="bg-tg-red text-white text-xs text-center py-2.5 flex items-center justify-center gap-2">
        <span className="animate-pulse">📡</span>
        Internet aloqasi yo'q
      </div>
    </div>
  )
}
