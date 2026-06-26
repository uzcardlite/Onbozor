import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { useUserStore, useAppStore } from './store/useStore'
import { useTelegram } from './hooks/useTelegram'
import { authAPI } from './api/endpoints'
import BottomNav from './components/BottomNav'
import OfflineBanner from './components/OfflineBanner'
import Home from './pages/Home'
import Onboarding from './pages/Onboarding'
import Search from './pages/Search'
import SectionPage from './pages/SectionPage'
import ListingDetail from './pages/ListingDetail'
import Shops from './pages/Shops'
import ShopDetail from './pages/ShopDetail'
import AddListing from './pages/AddListing'
import Favourites from './pages/Favourites'
import Referral from './pages/Referral'
import Profile from './pages/Profile'
import PaymentResult from './pages/PaymentResult'
import OpenShop from './pages/OpenShop'
import Leaderboard from './pages/Leaderboard'
import Messages from './pages/Messages'
import Chat from './pages/Chat'
import Admin from './pages/Admin'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000, refetchOnWindowFocus: false },
  },
})

const MOCK_USER = {
  id: 'mock-user-id',
  tg_id: 37453466,
  username: 'admin',
  full_name: 'Admin',
  viloyat: null,
  phone: null,
  avatar_url: null,
  ref_code: 'demo123',
  ref_count: 0,
  ref_earnings: 0,
  is_admin: true,
  created_at: new Date().toISOString(),
}

function AuthGate({ children }) {
  const { token, setToken, setUser } = useUserStore()
  const { onboarded } = useAppStore()
  const { initData, isTelegram, ready, expand } = useTelegram()

  useEffect(() => {
    if (isTelegram) {
      ready()
      expand()
    }
  }, [])

  useEffect(() => {
    if (token) return

    if (isTelegram && initData) {
      authAPI.telegram(initData).then((res) => {
        setToken(res.data.token)
        setUser(res.data.user)
      }).catch(() => {
        if (import.meta.env.DEV) {
          setToken('demo-token')
          setUser(MOCK_USER)
        }
      })
    } else if (import.meta.env.DEV) {
      setToken('demo-token')
      setUser(MOCK_USER)
    }
  }, [initData, token])

  if (!onboarded) return <Onboarding />
  if (!token) {
    return (
      <div className="min-h-screen bg-tg-bg flex items-center justify-center max-w-app mx-auto">
        <div className="text-center">
          <p className="text-3xl mb-4">⏳</p>
          <p className="text-sm text-tg-muted">Yuklanmoqda...</p>
        </div>
      </div>
    )
  }

  return children
}

function Layout() {
  return (
    <div className="min-h-screen bg-tg-bg max-w-app mx-auto relative">
      <OfflineBanner />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
        <Route path="/listings/:section" element={<SectionPage />} />
        <Route path="/listing/:id" element={<ListingDetail />} />
        <Route path="/shops" element={<Shops />} />
        <Route path="/shop/:id" element={<ShopDetail />} />
        <Route path="/add-listing" element={<AddListing />} />
        <Route path="/favourites" element={<Favourites />} />
        <Route path="/referral" element={<Referral />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/open-shop" element={<OpenShop />} />
        <Route path="/payment-result" element={<PaymentResult />} />
        <Route path="/messages" element={<Messages />} />
        <Route path="/messages/:id" element={<Chat />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
      <BottomNav />
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthGate>
          <Layout />
        </AuthGate>
        <Toaster
          position="top-center"
          toastOptions={{
            style: { background: '#2b2b2b', color: '#fff', fontSize: '13px', borderRadius: '12px' },
            success: { iconTheme: { primary: '#4ade80', secondary: '#fff' } },
            error: { iconTheme: { primary: '#f56565', secondary: '#fff' } },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
