import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { useUserStore, useAppStore } from './store/useStore'
import { useTelegram } from './hooks/useTelegram'
import { authAPI } from './api/endpoints'
import BottomNav from './components/BottomNav'
import OfflineBanner from './components/OfflineBanner'
import ErrorBoundary from './components/ErrorBoundary'

const Home = lazy(() => import('./pages/Home'))
const Onboarding = lazy(() => import('./pages/Onboarding'))
const Search = lazy(() => import('./pages/Search'))
const SectionPage = lazy(() => import('./pages/SectionPage'))
const ListingDetail = lazy(() => import('./pages/ListingDetail'))
const Shops = lazy(() => import('./pages/Shops'))
const ShopDetail = lazy(() => import('./pages/ShopDetail'))
const AddListing = lazy(() => import('./pages/AddListing'))
const Favourites = lazy(() => import('./pages/Favourites'))
const Referral = lazy(() => import('./pages/Referral'))
const Profile = lazy(() => import('./pages/Profile'))
const PaymentResult = lazy(() => import('./pages/PaymentResult'))
const OpenShop = lazy(() => import('./pages/OpenShop'))
const Leaderboard = lazy(() => import('./pages/Leaderboard'))
const Messages = lazy(() => import('./pages/Messages'))
const Chat = lazy(() => import('./pages/Chat'))
const Admin = lazy(() => import('./pages/Admin'))
const NotFound = lazy(() => import('./pages/NotFound'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 5 * 60 * 1000, refetchOnWindowFocus: false },
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
  is_verified: false,
  created_at: new Date().toISOString(),
}

function PageLoader() {
  return (
    <div className="min-h-screen bg-tg-bg flex items-center justify-center max-w-app mx-auto">
      <div className="w-8 h-8 border-2 border-tg-accent border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

function AuthGate({ children }) {
  const { token, setToken, setUser } = useUserStore()
  const { onboarded } = useAppStore()
  const { initData, isTelegram, ready, expand } = useTelegram()

  useEffect(() => {
    if (isTelegram) { ready(); expand() }
  }, [])

  useEffect(() => {
    if (token) return

    // Demo/owner login — gets a REAL JWT + user_id (so listing creation works)
    // instead of the fake 'demo-token' which carries no Authorization header.
    const demoLogin = () =>
      authAPI.demo(MOCK_USER.tg_id, { username: MOCK_USER.username, full_name: MOCK_USER.full_name })
        .then((res) => { setToken(res.data.token); setUser(res.data.user) })
        .catch(() => { setToken('demo-token'); setUser(MOCK_USER) })

    if (isTelegram && initData) {
      authAPI.telegram(initData)
        .then((res) => { setToken(res.data.token); setUser(res.data.user) })
        .catch(demoLogin)
    } else {
      demoLogin()
    }
  }, [initData, token])

  if (!onboarded) return <Suspense fallback={<PageLoader />}><Onboarding /></Suspense>
  if (!token) return <PageLoader />
  return children
}

function Layout() {
  return (
    <div className="min-h-screen bg-tg-bg max-w-app mx-auto relative">
      <OfflineBanner />
      <Suspense fallback={<PageLoader />}>
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
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
      <BottomNav />
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthGate>
          <Layout />
        </AuthGate>
        <Toaster
          position="top-center"
          toastOptions={{
            duration: 3000,
            style: { background: '#242F3D', color: '#fff', fontSize: '13px', borderRadius: '12px', border: '1px solid #2B3945' },
            success: { iconTheme: { primary: '#4ade80', secondary: '#fff' } },
            error: { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
    </ErrorBoundary>
  )
}
