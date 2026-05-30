export type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: number
  type: ToastType
  message: string
}

const toasts = ref<Toast[]>([])
let counter = 0

export const useToast = () => {
  const add = (message: string, type: ToastType = 'success', duration = 3500) => {
    const id = ++counter
    toasts.value.push({ id, type, message })
    setTimeout(() => remove(id), duration)
  }

  const remove = (id: number) => {
    const idx = toasts.value.findIndex(t => t.id === id)
    if (idx !== -1) toasts.value.splice(idx, 1)
  }

  return {
    toasts: readonly(toasts),
    success: (msg: string) => add(msg, 'success'),
    error:   (msg: string) => add(msg, 'error', 5000),
    warning: (msg: string) => add(msg, 'warning'),
    info:    (msg: string) => add(msg, 'info'),
    remove
  }
}
