import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import LoginView from '../LoginView.vue'

describe('LoginView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows invalid-credentials error and stays on login after a 401', async () => {
    const fetchMock = vi.fn<() => Promise<Response>>(async () =>
      Response.json(
        {
          type: 'about:blank',
          title: 'Unauthorized',
          status: 401,
          errors: { detail: 'No active account found with the given credentials' },
        },
        { status: 401, headers: { 'Content-Type': 'application/problem+json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/login', name: 'login', component: LoginView },
        { path: '/orders', name: 'orders', component: { template: '<div>orders</div>' } },
      ],
    })
    await router.push('/login?next=/orders')
    await router.isReady()
    const wrapper = mount(LoginView, { global: { plugins: [router] } })

    await wrapper.get('#username').setValue('ana')
    await wrapper.get('#password').setValue('wrong-password')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Utilizador ou palavra-passe inválidos.')
    expect(router.currentRoute.value.name).toBe('login')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})
