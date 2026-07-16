import { useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import './index.css'
import { ThemeProvider, useTheme } from './theme/ThemeProvider'
import { useCommandPalette } from './hooks/useCommandPalette'
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts'
import { CommandPalette } from './components/CommandPalette'
import { KeyboardShortcutsHelp } from './components/KeyboardShortcutsHelp'
import {
  BotIcon,

  FlaskConicalIcon,
  KeyboardIcon,
  LayoutDashboardIcon,
  MonitorIcon,
  MoonIcon,
  SunIcon,
  UsersIcon,
} from './components/icons'
import Dashboard from './pages/Dashboard'
import Studies from './pages/Studies'
import Subjects from './pages/Subjects'
import AgentSubjects from './pages/AgentSubjects'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: <LayoutDashboardIcon /> },
  { to: '/studies', label: 'Studies', icon: <FlaskConicalIcon /> },
  { to: '/subjects', label: 'Subjects', icon: <UsersIcon /> },
  { to: '/agents', label: 'Agent Subjects', icon: <BotIcon /> },
]

function AppShell() {
  const navigate = useNavigate()
  const location = useLocation()
  const { mode, resolved, toggle, setMode } = useTheme()
  const [shortcutsOpen, setShortcutsOpen] = useState(false)

  const commandCommands = [
    { id: 'go-dashboard', title: 'Go to Dashboard', section: 'Navigation', shortcut: 'G D', icon: <LayoutDashboardIcon />, action: () => navigate('/') },
    { id: 'go-studies', title: 'Go to Studies', section: 'Navigation', shortcut: 'G S', icon: <FlaskConicalIcon />, action: () => navigate('/studies') },
    { id: 'go-subjects', title: 'Go to Subjects', section: 'Navigation', shortcut: 'G U', icon: <UsersIcon />, action: () => navigate('/subjects') },
    { id: 'go-agents', title: 'Go to Agent Subjects', section: 'Navigation', shortcut: 'G A', icon: <BotIcon />, action: () => navigate('/agents') },
    { id: 'theme-light', title: 'Use light theme', section: 'Preferences', icon: <SunIcon />, action: () => setMode('light') },
    { id: 'theme-dark', title: 'Use dark theme', section: 'Preferences', icon: <MoonIcon />, action: () => setMode('dark') },
    { id: 'theme-system', title: 'Use system theme', section: 'Preferences', icon: <MonitorIcon />, action: () => setMode('system') },
    { id: 'show-shortcuts', title: 'Show keyboard shortcuts', section: 'Help', shortcut: '?', icon: <KeyboardIcon />, action: () => setShortcutsOpen(true) },
  ]

  const palette = useCommandPalette(commandCommands)

  const shortcuts = [
    { key: 'k', ctrl: true, description: 'Open command palette', handler: palette.openPalette },
    { key: 'd', ctrl: true, description: 'Go to Dashboard', handler: () => navigate('/') },
    { key: 's', ctrl: true, description: 'Go to Studies', handler: () => navigate('/studies') },
    { key: 'u', ctrl: true, description: 'Go to Subjects', handler: () => navigate('/subjects') },
    { key: 'a', ctrl: true, description: 'Go to Agent Subjects', handler: () => navigate('/agents') },
    { key: '?', description: 'Show keyboard shortcuts', handler: () => setShortcutsOpen(true) },
    { key: 't', ctrl: true, description: 'Toggle theme', handler: toggle },
  ]

  useKeyboardShortcuts(shortcuts)

  const ThemeIcon = mode === 'dark' ? MoonIcon : mode === 'light' ? SunIcon : MonitorIcon

  return (
    <div className="app" data-theme={resolved}>
      <nav className="sidebar" aria-label="Main navigation">
        <div className="sidebar__brand">
          <div className="sidebar__logo" aria-hidden="true">
            CT
          </div>
          <h1 className="sidebar__title">CTMS</h1>
        </div>

        <div>
          <div className="sidebar__subtitle">Workspace</div>
          <ul className="sidebar__nav">
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  className="sidebar__link"
                  aria-current={location.pathname === item.to ? 'page' : undefined}
                  data-action={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  {item.icon}
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>

        <div className="sidebar__footer">
          <button
            className="theme-toggle"
            onClick={toggle}
            aria-label={`Theme: ${mode}. Toggle.`}
            data-action="toggle-theme"
          >
            <ThemeIcon />
            <span className="capitalize">{mode}</span>
          </button>

          <button
            className="sidebar__command-hint"
            onClick={palette.openPalette}
            data-action="open-command-palette-hint"
          >
            <span>Command palette</span>
            <kbd>Ctrl K</kbd>
          </button>

          <Link
            to="https://github.com/symphonix-health/clinical-trial-system"
            target="_blank"
            rel="noopener noreferrer"
            className="sidebar__command-hint"
            data-action="open-help-docs"
          >
            <span>Documentation</span>
            <kbd>?</kbd>
          </Link>
        </div>
      </nav>

      <main className="main" id="main-content" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/studies" element={<Studies />} />
          <Route path="/subjects" element={<Subjects />} />
          <Route path="/agents" element={<AgentSubjects />} />
        </Routes>
      </main>

      <CommandPalette
        open={palette.open}
        onClose={palette.closePalette}
        query={palette.query}
        onQueryChange={palette.setQuery}
        grouped={palette.grouped}
      />

      <KeyboardShortcutsHelp
        open={shortcutsOpen}
        onClose={() => setShortcutsOpen(false)}
        shortcuts={shortcuts}
      />
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AppShell />
    </ThemeProvider>
  )
}

export default App
