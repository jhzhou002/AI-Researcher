import request from '../utils/request'

export const authApi = {
    async login(username, password) {
        const formData = new FormData()
        formData.append('username', username)
        formData.append('password', password)

        return request.post('/api/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
    },

    async register(email, username, password) {
        return request.post('/api/auth/register', {
            email,
            username,
            password
        })
    },

    async getMe() {
        return request.get('/api/auth/me')
    },

    async updateMe(data) {
        return request.put('/api/auth/me', data)
    }
}
