import { create } from 'zustand'

export const useUserStore = create((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  setUser: (user) => set({ user }),
  setToken: (token) => {
    localStorage.setItem('token', token)
    set({ token })
  },
  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null })
  },
}))

export const useAppStore = create((set) => ({
  onboarded: localStorage.getItem('onboarded') === 'true',
  selectedRegion: localStorage.getItem('region') || null,
  setOnboarded: () => {
    localStorage.setItem('onboarded', 'true')
    set({ onboarded: true })
  },
  setRegion: (region) => {
    localStorage.setItem('region', region)
    set({ selectedRegion: region })
  },
}))
