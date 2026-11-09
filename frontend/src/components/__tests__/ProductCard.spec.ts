import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ProductCard from '../ProductCard.vue'
import type { Product } from '@/types'

const product: Product = {
  id: 42,
  category: 3,
  category_name: 'Iluminação',
  name: 'Candeeiro de secretária',
  sku: 'SKU-0042',
  description: 'Luz para a secretária.',
  price: '24.50',
  stock: 8,
  is_active: true,
}

describe('ProductCard', () => {
  it('emite select com o id do produto ao clicar', async () => {
    const wrapper = mount(ProductCard, {
      props: { product: { ...product, name: 'Candeeiro <b>seguro</b>' } },
    })

    expect(wrapper.get('h2').text()).toBe('Candeeiro <b>seguro</b>')
    expect(wrapper.find('h2 b').exists()).toBe(false)

    await wrapper.get('button').trigger('click')

    expect(wrapper.emitted('select')).toEqual([[42]])
  })
})
