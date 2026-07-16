import { useEffect, useRef, useState } from 'react'
import type { Command } from '../hooks/useCommandPalette'
import { CommandIcon, SearchIcon, XIcon } from './icons'

interface CommandPaletteProps {
  open: boolean
  onClose: () => void
  query: string
  onQueryChange: (q: string) => void
  grouped: Map<string, Command[]>
}

export function CommandPalette({
  open,
  onClose,
  query,
  onQueryChange,
  grouped,
}: CommandPaletteProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const [selectedIndex, setSelectedIndex] = useState(0)

  useEffect(() => {
    if (open) {
      setSelectedIndex(0)
      inputRef.current?.focus()
    }
  }, [open])

  const flat = Array.from(grouped.values()).flat()

  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (!open) return
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
        return
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((i) => (i + 1) % Math.max(flat.length, 1))
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((i) => (i - 1 + Math.max(flat.length, 1)) % Math.max(flat.length, 1))
        return
      }
      if (e.key === 'Enter') {
        e.preventDefault()
        const cmd = flat[selectedIndex]
        if (cmd) {
          cmd.action()
          onClose()
        }
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, flat, selectedIndex, onClose])

  useEffect(() => {
    const active = listRef.current?.querySelector('[data-selected="true"]') as HTMLElement | null
    active?.scrollIntoView({ block: 'nearest' })
  }, [selectedIndex])

  if (!open) return null

  let globalIndex = 0

  return (
    <div
      className="command-palette"
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      data-testid="command-palette"
    >
      <div className="command-palette__panel">
        <div className="command-palette__input-row">
          <CommandIcon className="command-palette__icon" aria-hidden="true" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="Type a command or search…"
            className="command-palette__input"
            aria-label="Command search"
            data-action="command-input"
          />
          <button
            className="command-palette__close"
            onClick={onClose}
            aria-label="Close command palette"
            data-action="close-command-palette"
          >
            <XIcon />
          </button>
        </div>

        <div ref={listRef} className="command-palette__results" role="listbox">
          {flat.length === 0 && (
            <div className="command-palette__empty">
              <SearchIcon className="icon--lg" />
              <p>No commands match “{query}”</p>
            </div>
          )}
          {Array.from(grouped.entries()).map(([section, commands]) =>
            commands.length > 0 ? (
              <div key={section} className="command-palette__group" role="group" aria-label={section}>
                <div className="command-palette__section">{section}</div>
                {commands.map((cmd) => {
                  const index = globalIndex++
                  const isSelected = index === selectedIndex
                  return (
                    <button
                      key={cmd.id}
                      type="button"
                      className="command-palette__item"
                      data-selected={isSelected}
                      onMouseEnter={() => setSelectedIndex(index)}
                      onClick={() => {
                        cmd.action()
                        onClose()
                      }}
                      role="option"
                      aria-selected={isSelected}
                      data-action={`command-${cmd.id}`}
                    >
                      <span className="command-palette__item-icon" aria-hidden="true">
                        {cmd.icon}
                      </span>
                      <span className="command-palette__item-title">{cmd.title}</span>
                      {cmd.shortcut && (
                        <kbd className="command-palette__shortcut">{cmd.shortcut}</kbd>
                      )}
                    </button>
                  )
                })}
              </div>
            ) : null,
          )}
        </div>

        <div className="command-palette__footer">
          <span>
            <kbd>↑</kbd> <kbd>↓</kbd> to navigate
          </span>
          <span>
            <kbd>↵</kbd> to select
          </span>
          <span>
            <kbd>esc</kbd> to close
          </span>
        </div>
      </div>
    </div>
  )
}
