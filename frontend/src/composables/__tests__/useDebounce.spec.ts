import { effectScope, ref } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useDebounce } from '../useDebounce'

describe('useDebounce', () => {
  afterEach(() => vi.useRealTimers())

  it('publishes the latest value only after the delay', async () => {
    vi.useFakeTimers()
    const scope = effectScope()
    const source = ref('')
    let debounced!: ReturnType<typeof useDebounce<string>>

    scope.run(() => {
      debounced = useDebounce(source, 300)
    })

    source.value = 'desk'
    await vi.advanceTimersByTimeAsync(200)
    source.value = 'desk lamp'
    await vi.advanceTimersByTimeAsync(299)
    expect(debounced.value).toBe('')

    await vi.advanceTimersByTimeAsync(1)
    expect(debounced.value).toBe('desk lamp')
    scope.stop()
  })
})
