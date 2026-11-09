import { ref, watch, type Ref } from 'vue'

export function useDebounce<T>(source: Ref<T>, delay = 300): Ref<T> {
  const debounced = ref(source.value) as Ref<T>

  watch(source, (value, _previous, onCleanup) => {
    const timeout = setTimeout(() => {
      debounced.value = value
    }, delay)

    onCleanup(() => clearTimeout(timeout))
  })

  return debounced
}
