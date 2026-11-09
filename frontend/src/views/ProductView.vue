<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

import { getProduct } from '@/api/client'
import { useFetch } from '@/composables/useFetch'
import type { Product } from '@/types'

const props = defineProps<{ id: string }>()
const {
  data: product,
  error,
  loading,
  reload,
} = useFetch<Product>((signal) => getProduct(Number(props.id), signal))

const details = computed(() => {
  if (!product.value) return []
  return [
    { label: 'Referência', value: product.value.sku },
    { label: 'Categoria', value: product.value.category_name },
    {
      label: 'Disponibilidade',
      value: (product.value.stock ?? 0) > 0 ? 'Em stock' : 'Esgotado',
    },
    { label: 'Estado', value: product.value.is_active ? 'Ativo' : 'Indisponível' },
  ]
})
</script>

<template>
  <section class="product-detail">
    <RouterLink class="back-link" to="/products">← Voltar ao catálogo</RouterLink>

    <div v-if="loading" class="state-panel" role="status" aria-live="polite">
      <span class="spinner" aria-hidden="true"></span>
      <p>A carregar produto…</p>
    </div>

    <div v-else-if="error" class="state-panel state-panel--error" role="alert">
      <span class="state-icon" aria-hidden="true">!</span>
      <h1>Não foi possível carregar este produto</h1>
      <p>{{ error.message }}</p>
      <button class="button" type="button" @click="reload">Tentar novamente</button>
    </div>

    <article v-else-if="product" class="detail-card">
      <div class="detail-art" aria-hidden="true">
        <span>{{ product.category_name.slice(0, 1).toUpperCase() }}</span>
      </div>
      <div class="detail-copy">
        <p class="eyebrow">{{ product.category_name }} · {{ product.sku }}</p>
        <h1>{{ product.name }}</h1>
        <p class="detail-description">
          {{ product.description || 'Um produto selecionado para a tua casa.' }}
        </p>
        <p class="detail-price">{{ product.price }} €</p>
        <dl class="detail-list">
          <div v-for="item in details" :key="item.label">
            <dt>{{ item.label }}</dt>
            <dd>{{ item.value }}</dd>
          </div>
        </dl>
      </div>
    </article>
  </section>
</template>
