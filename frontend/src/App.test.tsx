import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import axios from 'axios'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

afterEach(() => {
  cleanup()
})

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    isAxiosError: vi.fn(),
  },
}))

describe('App', () => {
  it('renders navigation and dashboard', async () => {
    ;(axios.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { status: 'ok', version: '0.1.0', timestamp: new Date().toISOString() },
    })

    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: 'CTMS' })).toBeDefined()
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeDefined()
    })
  })

  it('opens command palette with Ctrl+K', async () => {
    ;(axios.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { status: 'ok', version: '0.1.0', timestamp: new Date().toISOString() },
    })

    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )

    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    await waitFor(() => {
      expect(screen.getByTestId('command-palette')).toBeDefined()
    })
  })

  it('shows keyboard shortcuts with ? key', async () => {
    ;(axios.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { status: 'ok', version: '0.1.0', timestamp: new Date().toISOString() },
    })

    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )

    fireEvent.keyDown(window, { key: '?' })
    await waitFor(() => {
      expect(screen.getByTestId('keyboard-shortcuts-help')).toBeDefined()
    })
  })
})
