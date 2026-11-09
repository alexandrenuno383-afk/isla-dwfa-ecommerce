import { api } from '@/api/client'

export function validProductSearchType() {
  return api.GET('/api/v1/products/', { params: { query: { search: 'lamp' } } })
}

export function invalidProductSearchType() {
  // @ts-expect-error Product filters are generated from the API schema; `foo` is not a filter.
  return api.GET('/api/v1/products/', { params: { query: { foo: 1 } } })
}
