import { watchEffect, shallowRef, ref } from 'vue'

export function useFetch<T>(load: (signal: AbortSignal) => Promise<T>) {
  const data = shallowRef<T | null>(null)
  const error = shallowRef<Error | null>(null)
  const loading = ref(true)
  const reloadVersion = ref(0)
  let activeController: AbortController | undefined

  watchEffect((onCleanup) => {
    void reloadVersion.value
    const controller = new AbortController()
    activeController = controller
    loading.value = true
    error.value = null
    data.value = null

    let request: Promise<T>
    try {
      request = load(controller.signal)
    } catch (reason) {
      error.value = reason instanceof Error ? reason : new Error(String(reason))
      loading.value = false
      return
    }

    void request
      .then((result) => {
        if (!controller.signal.aborted) data.value = result
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          error.value = reason instanceof Error ? reason : new Error(String(reason))
        }
      })
      .finally(() => {
        if (activeController === controller) loading.value = false
      })

    onCleanup(() => controller.abort())
  })

  function reload() {
    reloadVersion.value += 1
  }

  return { data, error, loading, reload }
}
