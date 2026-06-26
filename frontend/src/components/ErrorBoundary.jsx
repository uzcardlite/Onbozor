import { Component } from 'react'

export default class ErrorBoundary extends Component {
  state = { hasError: false }

  static getDerivedStateFromError() { return { hasError: true } }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-tg-bg flex items-center justify-center px-6 max-w-app mx-auto">
          <div className="text-center">
            <p className="text-5xl mb-4">😵</p>
            <h1 className="text-xl font-bold mb-2">Xatolik yuz berdi</h1>
            <p className="text-sm text-tg-muted mb-6">Nimadir xato ketdi. Sahifani yangilang.</p>
            <button onClick={() => { this.setState({ hasError: false }); window.location.reload() }} className="btn-primary">
              🔄 Qayta yuklash
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
