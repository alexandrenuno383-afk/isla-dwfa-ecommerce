import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { configureAuthTransport, getMe, obtainToken, rotateRefreshToken } from '@/api/client'
import type { Me } from '@/types'

export const useAuth = defineStore('auth', () => {
  const access = ref<string | null>(null)
  // Ficha 03 chose memory-only token storage, so refresh is deliberately not persisted.
  const refresh = ref<string | null>(null)
  const user = ref<Me | null>(null)
  const isReady = ref(false)
  const isLoggedIn = computed(() => user.value !== null)
  const isGestor = computed(() => user.value?.groups.includes('gestores') ?? false)

  function logout() {
    access.value = null
    refresh.value = null
    user.value = null
  }

  async function refreshAccess(): Promise<string | null> {
    if (!refresh.value) {
      logout()
      return null
    }

    try {
      const pair = await rotateRefreshToken(refresh.value)
      access.value = pair.access
      refresh.value = pair.refresh
      return access.value
    } catch {
      logout()
      return null
    }
  }

  async function login(username: string, password: string): Promise<Me> {
    const pair = await obtainToken(username, password)
    access.value = pair.access
    refresh.value = pair.refresh

    try {
      user.value = await getMe()
      return user.value
    } catch (error) {
      logout()
      throw error
    }
  }

  async function initialize() {
    try {
      if (refresh.value && (await refreshAccess())) {
        user.value = await getMe()
      }
    } catch {
      logout()
    } finally {
      isReady.value = true
    }
  }

  configureAuthTransport({ getAccessToken: () => access.value, refreshAccess })

  return {
    access,
    refresh,
    user,
    isReady,
    isLoggedIn,
    isGestor,
    login,
    logout,
    refreshAccess,
    initialize,
  }
})
