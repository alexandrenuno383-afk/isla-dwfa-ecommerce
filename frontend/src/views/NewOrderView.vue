<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { ApiError, createOrder, getAllProducts } from '@/api/client'
import { useFetch } from '@/composables/useFetch'
import { formatMinorUnits, toMinorUnits } from '@/utils/money'
import type { Product } from '@/types'

type OrderLine = { product: number; quantity: number }

const router = useRouter()
const {
  data: products,
  error: productsError,
  loading: productsLoading,
} = useFetch((signal) => getAllProducts(signal))
const lines = ref<OrderLine[]>([])
const sending = ref(false)
const formError = ref<Error | null>(null)
const quantityErrors = ref<Record<number, string>>({})

const availableProducts = computed(() =>
  (products.value ?? []).filter((product) => product.is_active !== false),
)

watch(availableProducts, (items) => {
  if (items.length && lines.value.length === 0) {
    lines.value = [{ product: items[0]!.id, quantity: 1 }]
  }
})

const totalCents = computed(() =>
  lines.value.reduce((total, line) => {
    const product = availableProducts.value.find((item) => item.id === line.product)
    return total + (product ? toMinorUnits(product.price) * line.quantity : 0)
  }, 0),
)

const formattedTotal = computed(() => formatMinorUnits(totalCents.value))

function addLine() {
  const unused = availableProducts.value.find(
    (product) => !lines.value.some((line) => line.product === product.id),
  )
  if (unused) lines.value.push({ product: unused.id, quantity: 1 })
}

function removeLine(index: number) {
  if (lines.value.length > 1) lines.value.splice(index, 1)
  quantityErrors.value = {}
}

function productOptions(line: OrderLine): Product[] {
  return availableProducts.value.filter(
    (product) =>
      product.id === line.product || !lines.value.some((item) => item.product === product.id),
  )
}

function describeFieldError(value: unknown): string {
  if (Array.isArray(value)) return value.map(describeFieldError).join(' ')
  return String(value)
}

function readQuantityErrors(reason: ApiError) {
  const errors = reason.problem.errors
  if (!errors || typeof errors !== 'object' || Array.isArray(errors)) return {}

  const items = (errors as Record<string, unknown>).items
  if (Array.isArray(items)) {
    return Object.fromEntries(
      items.flatMap((item, index) => {
        if (!item || typeof item !== 'object' || !('quantity' in item)) return []
        return [[index, describeFieldError(item.quantity)]]
      }),
    ) as Record<number, string>
  }
  const errorFields = errors as Record<string, unknown>
  if ('quantity' in errorFields) return { 0: describeFieldError(errorFields.quantity) }
  return {}
}

async function submitOrder() {
  formError.value = null
  quantityErrors.value = {}
  sending.value = true
  try {
    await createOrder(lines.value.map(({ product, quantity }) => ({ product, quantity })))
    await router.push({ name: 'orders' })
  } catch (reason) {
    if (reason instanceof ApiError && reason.status === 400) {
      quantityErrors.value = readQuantityErrors(reason)
      if (Object.keys(quantityErrors.value).length === 0) formError.value = reason
    } else {
      formError.value = reason instanceof Error ? reason : new Error(String(reason))
    }
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <section class="new-order-page">
    <RouterLink class="back-link" to="/orders">← Voltar às encomendas</RouterLink>
    <div class="page-heading">
      <p class="eyebrow">A tua próxima compra</p>
      <h1>Nova encomenda</h1>
      <p class="intro">
        Escolhe os produtos e as quantidades. O preço final é confirmado pela loja.
      </p>
    </div>

    <div v-if="productsLoading" class="state-panel" role="status" aria-live="polite">
      <span class="spinner" aria-hidden="true"></span>
      <p>A carregar produtos…</p>
    </div>
    <div v-else-if="productsError" class="state-panel state-panel--error" role="alert">
      <h2>Não foi possível carregar os produtos</h2>
      <p>{{ productsError.message }}</p>
    </div>
    <form v-else class="form-card order-form" @submit.prevent="submitOrder">
      <div class="form-section-heading">
        <div>
          <p class="eyebrow">Produtos</p>
          <h2>O que queres encomendar?</h2>
        </div>
        <button class="button button--quiet" type="button" @click="addLine">
          Adicionar produto +
        </button>
      </div>

      <div v-for="(line, index) in lines" :key="index" class="order-line">
        <label :for="`product-${index}`">Produto</label>
        <select :id="`product-${index}`" v-model.number="line.product" required>
          <option v-for="product in productOptions(line)" :key="product.id" :value="product.id">
            {{ product.name }} · {{ product.sku }} · {{ product.price }} €
          </option>
        </select>
        <label :for="`quantity-${index}`">Quantidade</label>
        <input
          :id="`quantity-${index}`"
          v-model.number="line.quantity"
          type="number"
          min="1"
          required
          @input="quantityErrors[index] = ''"
        />
        <button
          class="remove-line"
          type="button"
          :disabled="lines.length === 1"
          :aria-label="`Remover linha ${index + 1}`"
          @click="removeLine(index)"
        >
          Remover
        </button>
        <p v-if="quantityErrors[index]" class="field-error" role="alert">
          {{ quantityErrors[index] }}
        </p>
      </div>

      <p v-if="formError" class="form-error" role="alert">{{ formError.message }}</p>
      <div class="order-form__footer">
        <div>
          <span>Total estimado</span>
          <strong>{{ formattedTotal }} €</strong>
        </div>
        <button class="button" type="submit" :disabled="sending || !lines.length">
          {{ sending ? 'A criar encomenda…' : 'Confirmar encomenda' }}
        </button>
      </div>
      <p class="form-footnote">O total definitivo e o preço unitário são calculados pela API.</p>
    </form>
  </section>
</template>
