import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('token') || '')
    const user = ref(null)

    const isAuthenticated = computed(() => !!token.value)

    async function login(username, password) {
        try {
            const response = await authApi.login(username, password)
            token.value = response.access_token
            localStorage.setItem('token', response.access_token)
            await fetchUser()
            return { success: true }
        } catch (error) {
            return { success: false, error: error.response?.data?.detail || 'Login failed' }
        }
    }

    async function register(email, username, password) {
        try {
            await authApi.register(email, username, password)
            return { success: true }
        } catch (error) {
            return { success: false, error: error.response?.data?.detail || 'Registration failed' }
        }
    }

    async function fetchUser() {
        try {
            const userData = await authApi.getMe()
            user.value = userData
        } catch (error) {
            logout()
        }
    }

    function logout() {
        token.value = ''
        user.value = null
        localStorage.removeItem('token')
    }

    return {
        token,
        user,
        isAuthenticated,
        login,
        register,
        fetchUser,
        logout
    }
})
