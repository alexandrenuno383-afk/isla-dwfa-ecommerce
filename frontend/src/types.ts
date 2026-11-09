import type { components } from '@/api/schema'

export type Category = components['schemas']['Category']
export type Product = components['schemas']['Product']
export type Me = components['schemas']['Me']
export type Order = components['schemas']['Order']
export type OrderStatus = components['schemas']['OrderStatusEnum']
export type TokenPair = components['schemas']['TokenPair']
export type Problem = components['schemas']['ProblemDetails']

export interface Paginated<T> {
  count: number
  next?: string | null
  previous?: string | null
  results: T[]
}
