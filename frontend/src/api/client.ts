type ErrorEnvelope = {
  error: { code: string; message: string; request_id: string }
}

function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  if (typeof value !== 'object' || value === null || !('error' in value)) return false
  const error = value.error
  return typeof error === 'object' && error !== null &&
    'code' in error && typeof error.code === 'string' &&
    'message' in error && typeof error.message === 'string' &&
    'request_id' in error && typeof error.request_id === 'string'
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly requestId: string | null,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function getJson(path: string): Promise<unknown> {
  if (!path.startsWith('/api/') || path.includes('\\')) {
    throw new Error('API paths must start with /api/')
  }
  const response = await fetch(path, { credentials: 'same-origin' })
  let body: unknown
  try {
    body = await response.json()
  } catch (error) {
    if (!(error instanceof SyntaxError)) throw error
    throw new ApiError(response.status, 'INVALID_RESPONSE', 'Réponse API invalide.', response.headers.get('X-Request-ID'))
  }
  if (!response.ok) {
    if (isErrorEnvelope(body)) {
      throw new ApiError(response.status, body.error.code, body.error.message, body.error.request_id)
    }
    throw new ApiError(response.status, 'INVALID_RESPONSE', 'Réponse API invalide.', response.headers.get('X-Request-ID'))
  }
  return body
}

export async function getHealth(): Promise<{ status: 'ok' }> {
  const body = await getJson('/api/v1/health')
  if (typeof body !== 'object' || body === null || !('status' in body) || body.status !== 'ok') {
    throw new Error('Réponse de santé API invalide.')
  }
  return { status: body.status }
}
