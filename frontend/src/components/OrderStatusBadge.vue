<script setup lang="ts">
import type { OrderStatus } from '@/types'

const props = defineProps<{ status: OrderStatus }>()

const labels: Record<OrderStatus, { text: string; className: string }> = {
  pending: { text: 'Pendente', className: 'status-badge--pending' },
  paid: { text: 'Paga', className: 'status-badge--paid' },
  shipped: { text: 'Enviada', className: 'status-badge--shipped' },
  cancelled: { text: 'Cancelada', className: 'status-badge--cancelled' },
}
</script>

<template>
  <span class="status-badge" :class="labels[props.status].className">
    {{ labels[props.status].text }}
  </span>
</template>
