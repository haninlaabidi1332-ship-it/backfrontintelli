const isDark = ref(true)

export const useTheme = () => {
  const apply = (dark: boolean) => {
    isDark.value = dark
    if (dark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }

  const init = () => {
    const saved = localStorage.getItem('theme')
    apply(saved ? saved === 'dark' : true)
  }

  const toggle = () => apply(!isDark.value)

  return { isDark: readonly(isDark), toggle, init, apply }
}
