import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import OrderStatusBadge from '../OrderStatusBadge.vue'
import type { OrderStatus } from '@/types'

describe('OrderStatusBadge', () => {
  it.each([
    ['pending', 'Pendente'],
    ['paid', 'Paga'],
    ['shipped', 'Enviada'],
    ['cancelled', 'Cancelada'],
  ] as const)('mostra %s como %s', (status, label) => {
    const wrapper = mount(OrderStatusBadge, { props: { status: status as OrderStatus } })

    expect(wrapper.text()).toBe(label)
  })
})
