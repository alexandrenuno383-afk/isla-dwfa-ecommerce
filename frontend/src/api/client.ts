import createClient from 'openapi-fetch'

import type { paths } from '@/api/schema'
import type { Me, Order, OrderStatus, Paginated, Product, Problem } from '@/types'

const apiBaseUrl = import.meta.env.VITE_API_URL.replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly problem: Problem,
  ) {
    super(describeProblem(problem))
    this.name = 'ApiError'
  }
}

function describeProblem(problem: Problem): string {
  const errors = problem.errors
  if (Array.isArray(errors)) return errors.map(String).join(', ') || problem.title
  if (errors && typeof errors === 'object') {
    const entries = Object.entries(errors)
    if (entries.length === 1 && entries[0]?.[0] === 'detail') {
      return String(entries[0][1])
    }
    const messages = entries.map(([field, value]) => `${field}: ${formatError(value)}`)
    return messages.join(' · ') || problem.title
  }
  return problem.title
}

function formatError(value: unknown): string {
  if (Array.isArray(value)) return value.map(formatError).join(', ')
  if (value && typeof value === 'object') {
    return Object.entries(value)
      .map(([key, nested]) => `${key}: ${formatError(nested)}`)
      .join(', ')
  }
  return String(value)
}

function isProblem(value: unknown): value is Problem {
  if (!value || typeof value !== 'object') return false
  const candidate = value as Partial<Problem>
  return (
    typeof candidate.title === 'string' &&
    typeof candidate.status === 'number' &&
    'errors' in candidate
  )
}

async function toProblem(response: Response, body: unknown): Promise<Problem> {
  let candidate = body
  if (candidate === undefined)
    candidate = await response
      .clone()
      .json()
      .catch(() => null)
  if (isProblem(candidate)) return candidate
  return {
    type: 'about:blank',
    title: response.statusText || 'Pedido falhou',
    status: response.status,
    errors: candidate ?? { detail: 'A API devolveu uma resposta inválida.' },
  }
}

type AuthTransport = {
  getAccessToken: () => string | null
  refreshAccess: () => Promise<string | null>
  onSessionExpired?: () => void | Promise<void>
}

let authTransport: AuthTransport | undefined

export function configureAuthTransport(transport: AuthTransport) {
  authTransport = transport
}

function isTokenEndpoint(request: Request) {
  const path = new URL(request.url).pathname
  return path.endsWith('/api/v1/auth/token/') || path.endsWith('/api/v1/auth/token/refresh/')
}

async function authenticatedFetch(input: Request): Promise<Response> {
  const request = input.clone()
  const access = authTransport?.getAccessToken()
  if (access && !isTokenEndpoint(request)) {
    request.headers.set('Authorization', `Bearer ${access}`)
  }

  const response = await fetch(request)
  if (response.status !== 401 || isTokenEndpoint(request) || !authTransport) return response

  const refreshedAccess = await authTransport.refreshAccess()
  if (!refreshedAccess) {
    await authTransport.onSessionExpired?.()
    return response
  }

  const retry = input.clone()
  retry.headers.set('Authorization', `Bearer ${refreshedAccess}`)
  const retryResponse = await fetch(retry)
  if (retryResponse.status === 401) await authTransport.onSessionExpired?.()
  return retryResponse
}

export const api = createClient<paths>({
  baseUrl: apiBaseUrl,
  headers: { Accept: 'application/json' },
  fetch: authenticatedFetch,
})

type ApiResult<T> = { data?: T; error?: unknown; response: Response }

async function unwrap<T>(request: Promise<ApiResult<T>>): Promise<T> {
  const result = await request
  if (!result.response.ok) {
    throw new ApiError(result.response.status, await toProblem(result.response, result.error))
  }
  if (result.data === undefined) {
    throw new ApiError(result.response.status, {
      type: 'about:blank',
      title: 'Resposta vazia',
      status: result.response.status,
      errors: { detail: 'A API não devolveu os dados esperados.' },
    })
  }
  return result.data
}

export function obtainToken(username: string, password: string) {
  return unwrap(
    api.POST('/api/v1/auth/token/', {
      body: { username, password },
    }),
  )
}

export function rotateRefreshToken(refresh: string) {
  return unwrap(
    api.POST('/api/v1/auth/token/refresh/', {
      body: { refresh },
    }),
  )
}

export function getMe(): Promise<Me> {
  return unwrap(api.GET('/api/v1/me/'))
}

export function getProductsPage(search?: string, page = 1, signal?: AbortSignal) {
  return unwrap(
    api.GET('/api/v1/products/', {
      params: { query: { search, page } },
      signal,
    }),
  )
}

export function getProducts(
  search?: string,
  page = 1,
  signal?: AbortSignal,
): Promise<Paginated<Product>> {
  return getProductsPage(search, page, signal)
}

export async function getAllProducts(signal?: AbortSignal): Promise<Product[]> {
  const products: Product[] = []
  let page = 1
  let hasNextPage = true

  while (hasNextPage) {
    const result = await getProductsPage(undefined, page, signal)
    products.push(...result.results)
    hasNextPage = result.next != null
    page += 1
  }

  return products
}

export function getProduct(id: number, signal?: AbortSignal) {
  return unwrap(api.GET('/api/v1/products/{id}/', { params: { path: { id } }, signal }))
}

export function getOrders(signal?: AbortSignal): Promise<Paginated<Order>> {
  return unwrap(api.GET('/api/v1/orders/', { signal }))
}

export function createOrder(items: Array<{ product: number; quantity: number }>) {
  return unwrap(api.POST('/api/v1/orders/', { body: { items } }))
}

export function payOrder(id: number) {
  return unwrap(api.POST('/api/v1/orders/{id}/pay/', { params: { path: { id } } }))
}

export type { OrderStatus }
