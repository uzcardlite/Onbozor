const isTelegram = typeof window !== 'undefined' && window.Telegram?.WebApp?.initData

let tg = null
if (isTelegram) {
  tg = window.Telegram.WebApp
}

export function useTelegram() {
  const haptic = (type = 'impact', style = 'light') => {
    try {
      if (!tg) return
      if (type === 'impact') tg.HapticFeedback.impactOccurred(style)
      else if (type === 'notification') tg.HapticFeedback.notificationOccurred(style)
      else tg.HapticFeedback.selectionChanged()
    } catch {}
  }

  return {
    tg,
    isTelegram: !!isTelegram,
    initData: tg?.initData || '',
    user: tg?.initDataUnsafe?.user || null,
    haptic,
    close: () => tg?.close(),
    expand: () => tg?.expand(),
    ready: () => tg?.ready(),
  }
}
