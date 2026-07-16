import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

export type ThemeMode = 'light' | 'dark' | 'system'

interface ThemeContextValue {
  mode: ThemeMode
  resolved: 'light' | 'dark'
  setMode: (mode: ThemeMode) => void
  toggle: () => void
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined)

const STORAGE_KEY = 'ctms-theme-mode'

function resolveSystem(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light'
  if (typeof window.matchMedia !== 'function') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(() => {
    if (typeof window === 'undefined') return 'system'
    return (localStorage.getItem(STORAGE_KEY) as ThemeMode) || 'system'
  })
  const [resolved, setResolved] = useState<'light' | 'dark'>(resolveSystem)

  useEffect(() => {
    const root = document.documentElement
    const nextResolved = mode === 'system' ? resolveSystem() : mode
    setResolved(nextResolved)
    root.classList.remove('theme-light', 'theme-dark')
    root.classList.add(`theme-${nextResolved}`)
    root.setAttribute('data-theme', nextResolved)
    localStorage.setItem(STORAGE_KEY, mode)
    // Keep meta theme-color in sync with Symphonix brand tint.
    const metaTheme = document.querySelector('meta[name="theme-color"]')
    if (metaTheme) {
      metaTheme.setAttribute('content', nextResolved === 'dark' ? '#080a2e' : '#6366F1')
    }
  }, [mode])

  useEffect(() => {
    if (mode !== 'system') return
    if (typeof window.matchMedia !== 'function') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => setResolved(resolveSystem())
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [mode])

  const setMode = (next: ThemeMode) => setModeState(next)
  const toggle = () => {
    const order: ThemeMode[] = ['light', 'dark', 'system']
    const idx = order.indexOf(mode)
    setModeState(order[(idx + 1) % order.length])
  }

  return (
    <ThemeContext.Provider value={{ mode, resolved, setMode, toggle }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
