import WebApp from '@twa-dev/sdk'

export function useTelegram() {
  const tg = WebApp

  const haptic = (type = 'impact', style = 'light') => {
    try {
      if (type === 'impact') tg.HapticFeedback.impactOccurred(style)
      else if (type === 'notification') tg.HapticFeedback.notificationOccurred(style)
      else tg.HapticFeedback.selectionChanged()
    } catch {}
  }

  return {
    tg,
    initData: tg.initData,
    user: tg.initDataUnsafe?.user,
    haptic,
    close: () => tg.close(),
    expand: () => tg.expand(),
    ready: () => tg.ready(),
  }
}
