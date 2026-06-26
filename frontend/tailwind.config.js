/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        tg: {
          bg: '#17212B',
          card: '#242F3D',
          header: '#1C2733',
          accent: '#2AABEE',
          green: '#4ade80',
          yellow: '#f59e0b',
          red: '#ef4444',
          muted: '#708499',
          border: '#2B3945',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      maxWidth: {
        app: '430px',
      },
      keyframes: {
        'slide-up': {
          from: { transform: 'translateY(100%)', opacity: '0' },
          to: { transform: 'translateY(0)', opacity: '1' },
        },
        'slide-left': {
          from: { transform: 'translateX(30px)', opacity: '0' },
          to: { transform: 'translateX(0)', opacity: '1' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'pulse-heart': {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.3)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'count-up': {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'slide-up': 'slide-up 0.3s ease-out',
        'slide-left': 'slide-left 0.25s ease-out',
        'fade-in': 'fade-in 0.2s ease-out',
        'pulse-heart': 'pulse-heart 0.4s ease-in-out',
        'shimmer': 'shimmer 1.5s infinite linear',
        'count-up': 'count-up 0.5s ease-out',
      },
    },
  },
  plugins: [],
}
