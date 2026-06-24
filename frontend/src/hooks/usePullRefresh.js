import { useEffect, useRef, useState } from 'react'

export function usePullRefresh(onRefresh) {
  const [refreshing, setRefreshing] = useState(false)
  const startY = useRef(0)

  useEffect(() => {
    const onTouchStart = (e) => { startY.current = e.touches[0].clientY }
    const onTouchEnd = async (e) => {
      const diff = e.changedTouches[0].clientY - startY.current
      if (diff > 80 && window.scrollY === 0 && !refreshing) {
        setRefreshing(true)
        await onRefresh()
        setRefreshing(false)
      }
    }
    window.addEventListener('touchstart', onTouchStart)
    window.addEventListener('touchend', onTouchEnd)
    return () => {
      window.removeEventListener('touchstart', onTouchStart)
      window.removeEventListener('touchend', onTouchEnd)
    }
  }, [onRefresh, refreshing])

  return refreshing
}
