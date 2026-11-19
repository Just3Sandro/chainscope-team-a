import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

function renderApp(path = '/') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}><App /></MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ChainScope', () => {
  it('affiche le chargement puis la santé fournie par l’API', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'ok' })))
    vi.stubGlobal('fetch', fetchMock)
    renderApp()
    expect(screen.getByRole('heading', { name: 'ChainScope' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Vérification en cours')
    expect(await screen.findByText('API opérationnelle.')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/health', { credentials: 'same-origin' })
  })

  it('affiche une erreur accessible lorsque l’API échoue', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Unavailable')))
    renderApp()
    expect(await screen.findByRole('alert')).toHaveTextContent('API est indisponible')
  })

  it('affiche une page 404 pour une route inconnue', () => {
    renderApp('/inconnue')
    expect(screen.getByRole('heading', { name: 'Page introuvable' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Retour à l’accueil' })).toHaveAttribute('href', '/')
  })
})
