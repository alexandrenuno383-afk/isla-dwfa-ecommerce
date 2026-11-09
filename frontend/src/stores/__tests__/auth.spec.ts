import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuth } from '../auth'

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('stores the token pair in memory and loads the authenticated user', async () => {
    let meAuthorization: string | null = null
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async (request) => {
      const path = new URL(request.url).pathname
      if (path.endsWith('/auth/token/')) {
        return Response.json({ access: 'access-token', refresh: 'refresh-token' })
      }
      if (path.endsWith('/me/')) {
        meAuthorization = request.headers.get('Authorization')
        return Response.json({ id: 7, username: 'ana', groups: [] })
      }
      return Response.json({ detail: `Unexpected request ${path}` }, { status: 404 })
    })
    vi.stubGlobal('fetch', fetchMock)

    const auth = useAuth()
    await auth.login('ana', 'pass1234')

    expect(auth.user).toEqual({ id: 7, username: 'ana', groups: [] })
    expect(auth.access).toBe('access-token')
    expect(auth.refresh).toBe('refresh-token')
    expect(localStorage.getItem('refresh')).toBeNull()
    expect(meAuthorization).toBe('Bearer access-token')
  })
})
