<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ProductCard from '@/components/ProductCard.vue'
import { getProducts } from '@/api/client'
import { useDebounce } from '@/composables/useDebounce'
import { useFetch } from '@/composables/useFetch'

const route = useRoute()
const router = useRouter()

const search = computed({
  get: () => (typeof route.query.search === 'string' ? route.query.search : ''),
  set: (value: string) => {
    void router.replace({
      query: {
        ...route.query,
        search: value.trim() || undefined,
        page: undefined,
      },
    })
  },
})

const searchInput = ref(search.value)
const debouncedSearch = useDebounce(searchInput)

watch(search, (value) => {
  if (value !== searchInput.value) searchInput.value = value
})

watch(debouncedSearch, (value) => {
  if (value.trim() !== search.value) search.value = value
})

const page = computed(() => {
  const value = route.query.page
  const parsed = typeof value === 'string' ? Number.parseInt(value, 10) : 1
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 1
})

const { data, error, loading, reload } = useFetch((signal) =>
  getProducts(search.value || undefined, page.value, signal),
)

function openProduct(id: number) {
  void router.push({ name: 'product-detail', params: { id } })
}

function followPage(url: string | null | undefined) {
  if (!url) return
  const nextPage = new URL(url, import.meta.env.VITE_API_URL).searchParams.get('page')
  void router.push({
    query: {
      ...route.query,
      page: nextPage && nextPage !== '1' ? nextPage : undefined,
    },
  })
}
</script>

<template>
  <section class="catalogue">
    <div class="page-heading">
      <p class="eyebrow">A seleção da semana</p>
      <h1>Encontra o que <span>precisas.</span></h1>
      <p class="intro">Peças úteis para o dia a dia, escolhidas com cuidado.</p>
    </div>

    <form class="search-form" role="search" @submit.prevent>
      <label for="product-search">Pesquisar produtos</label>
      <div class="search-control">
        <span aria-hidden="true">⌕</span>
        <input
          id="product-search"
          v-model="searchInput"
          type="search"
          name="search"
          placeholder="Nome, SKU ou descrição"
          autocomplete="off"
        />
        <button v-if="searchInput" class="clear-search" type="button" @click="searchInput = ''">
          Limpar
        </button>
      </div>
    </form>

    <div v-if="loading" class="state-panel" role="status" aria-live="polite">
      <span class="spinner" aria-hidden="true"></span>
      <p>A carregar produtos…</p>
    </div>

    <div v-else-if="error" class="state-panel state-panel--error" role="alert">
      <span class="state-icon" aria-hidden="true">!</span>
      <h2>Não foi possível carregar o catálogo</h2>
      <p>{{ error.message }}</p>
      <button class="button" type="button" @click="reload">Tentar novamente</button>
    </div>

    <template v-else-if="data">
      <div class="results-heading">
        <h2>{{ search ? 'Resultados da pesquisa' : 'Todos os produtos' }}</h2>
        <span>{{ data.count }} {{ data.count === 1 ? 'produto' : 'produtos' }}</span>
      </div>

      <div v-if="data.results.length" class="product-grid">
        <ProductCard
          v-for="product in data.results"
          :key="product.id"
          :product="product"
          @select="openProduct"
        />
      </div>
      <div v-else class="state-panel state-panel--empty">
        <h2>Não encontrámos produtos</h2>
        <p>Experimenta outra pesquisa.</p>
      </div>

      <nav class="pagination" aria-label="Paginação de produtos">
        <button
          class="button button--quiet"
          type="button"
          :disabled="!data.previous"
          @click="followPage(data.previous)"
        >
          ← Anterior
        </button>
        <span>Página {{ page }}</span>
        <button
          class="button button--quiet"
          type="button"
          :disabled="!data.next"
          @click="followPage(data.next)"
        >
          Seguinte →
        </button>
      </nav>
    </template>
  </section>
</template>
