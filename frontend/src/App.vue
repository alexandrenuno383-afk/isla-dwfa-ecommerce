<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from 'vue-router'

import { useAuth } from '@/stores/auth'

const auth = useAuth()
const router = useRouter()

function logout() {
  auth.logout()
  void router.push({ name: 'login' })
}
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <RouterLink class="brand" to="/products" aria-label="DWFA Store, catálogo">
        <span class="brand-mark">D</span>
        <span>DWFA <strong>Store</strong></span>
      </RouterLink>
      <nav aria-label="Navegação principal">
        <RouterLink to="/products">Catálogo</RouterLink>
        <RouterLink v-if="auth.isLoggedIn" to="/orders">As minhas encomendas</RouterLink>
        <RouterLink v-if="auth.isLoggedIn" to="/orders/new">Nova encomenda</RouterLink>
      </nav>
      <div class="account-actions">
        <span v-if="auth.user" class="account-name">Olá, {{ auth.user.username }}</span>
        <RouterLink v-else class="login-link" to="/login">Entrar</RouterLink>
        <button v-if="auth.isLoggedIn" class="logout-button" type="button" @click="logout">
          Sair
        </button>
      </div>
    </header>
    <main class="page-content">
      <RouterView />
    </main>
    <footer class="site-footer">Uma loja de demonstração · ISLA Gaia</footer>
  </div>
</template>
