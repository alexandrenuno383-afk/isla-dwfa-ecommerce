<script setup lang="ts">
import type { Product } from '@/types'

defineProps<{ product: Product }>()
defineEmits<{ select: [id: number] }>()
</script>

<template>
  <article class="product-card">
    <div class="product-card__topline">
      <span class="product-category">{{ product.category_name }}</span>
      <span class="product-sku">{{ product.sku }}</span>
    </div>
    <h2>{{ product.name }}</h2>
    <p class="product-description">
      {{ product.description || 'Um produto selecionado para a tua casa.' }}
    </p>
    <div class="product-card__bottom">
      <span class="product-price">{{ product.price }} €</span>
      <button class="button button--quiet" type="button" @click="$emit('select', product.id)">
        Ver produto <span aria-hidden="true">→</span>
      </button>
    </div>
  </article>
</template>
