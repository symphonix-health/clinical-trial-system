import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export interface Command {
  id: string
  title: string
  section: string
  shortcut?: string
  icon?: React.ReactNode
  action: () => void
}

export function useCommandPalette(commands: Command[]) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return commands
    return commands.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        c.section.toLowerCase().includes(q) ||
        (c.shortcut && c.shortcut.toLowerCase().includes(q)),
    )
  }, [commands, query])

  const grouped = useMemo(() => {
    const map = new Map<string, Command[]>()
    for (const c of filtered) {
      const list = map.get(c.section) || []
      list.push(c)
      map.set(c.section, list)
    }
    return map
  }, [filtered])

  const openPalette = useCallback(() => setOpen(true), [])
  const closePalette = useCallback(() => {
    setOpen(false)
    setQuery('')
  }, [])

  return {
    open,
    setOpen,
    query,
    setQuery,
    grouped,
    filtered,
    openPalette,
    closePalette,
    navigate,
  }
}
