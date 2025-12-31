import request from '../utils/request'

export const projectsApi = {
    async list() {
        return request.get('/api/projects/')
    },

    async get(id) {
        return request.get(`/api/projects/${id}`)
    },

    async create(data) {
        return request.post('/api/projects/', data)
    },

    async update(id, data) {
        return request.put(`/api/projects/${id}`, data)
    },

    async delete(id) {
        return request.delete(`/api/projects/${id}`)
    },

    async getPapers(id) {
        return request.get(`/api/projects/${id}/papers`)
    },

    async getIdeas(id) {
        return request.get(`/api/projects/${id}/ideas`)
    }
}
