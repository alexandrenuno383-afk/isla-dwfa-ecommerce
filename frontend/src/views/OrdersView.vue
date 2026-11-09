<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'

import { ApiError, getOrders, payOrder } from '@/api/client'
import OrderStatusBadge from '@/components/OrderStatusBadge.vue'
import { useFetch } from '@/composables/useFetch'
import type { Order } from '@/types'

const { data, error, loading, reload } = useFetch((signal) => getOrders(signal))
const payingId = ref<number | null>(null)
const paymentErrors = ref<Record<number, string>>({})

async function pay(order: Order) {
  payingId.value = order.id
  paymentErrors.value[order.id] = ''
  try {
    await payOrder(order.id)
    reload()
  } catch (reason) {
    if (reason instanceof ApiError && reason.status === 409) {
      paymentErrors.value[order.id] = reason.message
    } else {
      paymentErrors.value[order.id] =
        reason instanceof Error ? reason.message : 'Não foi possível pagar a encomenda.'
    }
  } finally {
    payingId.value = null
  }
}
</script>

<template>
  <section class="orders-page">
    <div class="orders-heading">
      <div>
        <p class="eyebrow">A tua conta</p>
        <h1>As minhas encomendas</h1>
        <p class="intro">Consulta os pedidos e o estado de cada compra.</p>
      </div>
      <RouterLink class="button" to="/orders/new">Nova encomenda <span>+</span></RouterLink>
    </div>

    <div v-if="loading" class="state-panel" role="status" aria-live="polite">
      <span class="spinner" aria-hidden="true"></span>
      <p>A carregar encomendas…</p>
    </div>
    <div v-else-if="error" class="state-panel state-panel--error" role="alert">
      <span class="state-icon" aria-hidden="true">!</span>
      <h2>Não foi possível carregar as encomendas</h2>
      <p>{{ error.message }}</p>
      <button class="button" type="button" @click="reload">Tentar novamente</button>
    </div>
    <div v-else-if="data && data.results.length === 0" class="state-panel state-panel--empty">
      <h2>Ainda não tens encomendas</h2>
      <p>Quando fizeres uma compra, ela aparecerá aqui.</p>
      <RouterLink class="button" to="/orders/new">Criar encomenda</RouterLink>
    </div>
    <div v-else-if="data" class="orders-list">
      <article v-for="order in data.results" :key="order.id" class="order-card">
        <div class="order-card__header">
          <div>
            <p class="order-reference">Encomenda #{{ order.id }}</p>
            <p class="order-date">{{ new Date(order.created_at).toLocaleDateString('pt-PT') }}</p>
          </div>
          <OrderStatusBadge :status="order.status" />
        </div>
        <ul class="order-items">
          <li v-for="item in order.items" :key="item.id">
            <span>{{ item.quantity }} × {{ item.product_name }}</span>
            <span>{{ item.unit_price }} €</span>
          </li>
        </ul>
        <div class="order-card__footer">
          <div>
            <span class="order-total-label">Total</span>
            <strong>{{ order.total }} €</strong>
          </div>
          <button
            class="button"
            type="button"
            :disabled="payingId === order.id"
            @click="pay(order)"
          >
            {{
              payingId === order.id
                ? 'A processar…'
                : order.status === 'pending'
                  ? 'Pagar'
                  : 'Tentar pagar outra vez'
            }}
          </button>
        </div>
        <p v-if="paymentErrors[order.id]" class="form-error" role="alert">
          {{ paymentErrors[order.id] }}
        </p>
      </article>
      <p class="orders-count">{{ data.count }} encomendas</p>
    </div>
  </section>
</template>
