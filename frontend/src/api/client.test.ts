import { describe, expect, it, vi } from 'vitest'
import { ApiError, getHealth, getJson } from './client'

describe('client API', () => {
  it('conserve le code et le request ID d’une erreur normalisée', async () => {
    const requestId = 'e604f91f-d681-47e9-b3d1-0554ae14751e'
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      error: { code: 'FORBIDDEN', message: 'Accès refusé.', request_id: requestId },
    }), { status: 403 })))
    const response = getJson('/api/v1/private')
    await expect(response).rejects.toBeInstanceOf(ApiError)
    await expect(response).rejects.toMatchObject({
      status: 403, code: 'FORBIDDEN', requestId,
    })
  })

  it.each(['proxy-request-id', null])('normalise une réponse HTML 502 avec le request ID %s', async (requestId) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>Bad Gateway</html>', {
      status: 502,
      headers: {
        'Content-Type': 'text/html',
        ...(requestId === null ? {} : { 'X-Request-ID': requestId }),
      },
    })))
    const response = getJson('/api/v1/health')
    await expect(response).rejects.toBeInstanceOf(ApiError)
    await expect(response).rejects.toMatchObject({
      status: 502, code: 'INVALID_RESPONSE', message: 'Réponse API invalide.', requestId,
    })
  })

  it('refuse une réponse de santé inattendue', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'broken' }))))
    await expect(getHealth()).rejects.toThrow('Réponse de santé API invalide.')
  })

  it('refuse une URL externe avant tout appel réseau', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    await expect(getJson('https://example.test/api/')).rejects.toThrow('API paths')
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
