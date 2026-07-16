import { useEffect } from 'react'
import { KeyboardIcon, XIcon } from './icons'
import { Card } from './Card'
import type { Shortcut } from '../hooks/useKeyboardShortcuts'

interface KeyboardShortcutsHelpProps {
  open: boolean
  onClose: () => void
  shortcuts: Shortcut[]
}

export function KeyboardShortcutsHelp({ open, onClose, shortcuts }: KeyboardShortcutsHelpProps) {
  useEffect(() => {
    if (!open) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])

  if (!open) return null

  const formatShortcut = (s: Shortcut) => {
    const parts: string[] = []
    if (s.ctrl || s.meta) parts.push('Ctrl')
    if (s.shift) parts.push('Shift')
    if (s.alt) parts.push('Alt')
    parts.push(s.key.length === 1 ? s.key.toUpperCase() : s.key)
    return parts.join(' + ')
  }

  return (
    <div
      className="shortcuts-modal"
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      data-testid="keyboard-shortcuts-help"
    >
      <Card className="shortcuts-modal__panel" padding="lg">
        <div className="shortcuts-modal__header">
          <KeyboardIcon className="shortcuts-modal__icon" aria-hidden="true" />
          <h2>Keyboard shortcuts</h2>
          <button
            className="shortcuts-modal__close"
            onClick={onClose}
            aria-label="Close shortcuts"
            data-action="close-shortcuts"
          >
            <XIcon />
          </button>
        </div>
        <dl className="shortcuts-modal__list">
          {shortcuts.map((s, i) => (
            <div key={i} className="shortcuts-modal__row">
              <dt>{s.description}</dt>
              <dd>
                <kbd>{formatShortcut(s)}</kbd>
              </dd>
            </div>
          ))}
        </dl>
      </Card>
    </div>
  )
}
