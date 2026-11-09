<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import { useAuth } from '@/stores/auth'

const auth = useAuth()
const route = useRoute()
const router = useRouter()
const username = ref('')
const password = ref('')
const sending = ref(false)
const error = ref<Error | null>(null)

const errorMessage = computed(() => {
  if (error.value instanceof ApiError) {
    if (error.value.status === 401) return 'Utilizador ou palavra-passe inválidos.'
    if (error.value.status === 429)
      return 'Demasiadas tentativas. Aguarda um minuto e tenta novamente.'
  }
  return error.value?.message ?? ''
})

async function submitLogin() {
  sending.value = true
  error.value = null
  try {
    await auth.login(username.value, password.value)
    const requestedPath = route.query.next
    const next =
      typeof requestedPath === 'string' &&
      requestedPath.startsWith('/') &&
      !requestedPath.startsWith('//')
        ? requestedPath
        : '/orders'
    await router.push(next)
  } catch (reason) {
    error.value = reason instanceof Error ? reason : new Error(String(reason))
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <section class="auth-layout">
    <div class="auth-aside">
      <p class="eyebrow">Bem-vinda de volta</p>
      <h1>Entra na tua conta.</h1>
      <p>Acompanha encomendas e prepara a tua próxima compra.</p>
    </div>
    <form class="form-card login-form" @submit.prevent="submitLogin">
      <div>
        <p class="eyebrow">A tua conta</p>
        <h2>Iniciar sessão</h2>
      </div>
      <label for="username">Utilizador</label>
      <input
        id="username"
        v-model.trim="username"
        name="username"
        type="text"
        autocomplete="username"
        required
      />
      <label for="password">Palavra-passe</label>
      <input
        id="password"
        v-model="password"
        name="password"
        type="password"
        autocomplete="current-password"
        required
      />
      <p v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</p>
      <button class="button login-submit" type="submit" :disabled="sending">
        {{ sending ? 'A entrar…' : 'Entrar' }}
      </button>
    </form>
  </section>
</template>
