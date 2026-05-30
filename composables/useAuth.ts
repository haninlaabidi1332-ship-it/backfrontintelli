export const useAuthStore = () => {
  const accessToken = useCookie('access_token', { maxAge: 3600 })
  const refreshToken = useCookie('refresh_token', { maxAge: 604800 })
  const isAuthenticated = computed(() => !!accessToken.value)

  const login = async (email: string, password: string) => {
    const { data } = await useApi().post('/auth/jwt/token/', { email, password })
    accessToken.value = data.access
    refreshToken.value = data.refresh
    return data
  }

  const logout = () => {
    accessToken.value = null
    refreshToken.value = null
    navigateTo('/login')
  }

  return { isAuthenticated, login, logout, accessToken }
}
