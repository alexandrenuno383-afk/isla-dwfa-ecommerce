<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <section class="state-panel state-panel--empty not-found">
    <p class="eyebrow">Erro 404</p>
    <h1>Esta página não existe</h1>
    <p>O endereço pode estar incorreto ou a página foi movida.</p>
    <RouterLink class="button" to="/products">Ir para o catálogo</RouterLink>
  </section>
</template>
