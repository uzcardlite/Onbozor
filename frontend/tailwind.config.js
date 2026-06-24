/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        tg: {
          bg: '#212121',
          card: '#2b2b2b',
          header: '#1c2733',
          accent: '#2AABEE',
          green: '#4ade80',
          yellow: '#e8b94a',
          red: '#f56565',
          muted: '#8d8d8d',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      maxWidth: {
        app: '430px',
      }
    },
  },
  plugins: [],
}
