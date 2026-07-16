import { useEffect, useRef } from 'react'

export interface Shortcut {
  key: string
  ctrl?: boolean
  meta?: boolean
  shift?: boolean
  alt?: boolean
  handler: (e: KeyboardEvent) => void
  description: string
}

function matches(event: KeyboardEvent, shortcut: Shortcut): boolean {
  const key = event.key.toLowerCase()
  const target = event.target as HTMLElement | null
  if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) {
    if (!shortcut.ctrl && !shortcut.meta && !shortcut.alt) return false
  }
  return (
    key === shortcut.key.toLowerCase() &&
    !!event.ctrlKey === !!shortcut.ctrl &&
    !!event.metaKey === !!shortcut.meta &&
    !!event.shiftKey === !!shortcut.shift &&
    !!event.altKey === !!shortcut.alt
  )
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  const shortcutsRef = useRef(shortcuts)
  shortcutsRef.current = shortcuts

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      for (const s of shortcutsRef.current) {
        if (matches(e, s)) {
          e.preventDefault()
          s.handler(e)
          return
        }
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])
}
