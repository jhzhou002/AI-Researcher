import request from '../utils/request'

export const workflowsApi = {
    // 文献检索
    async startDiscovery(projectId, maxResults = 50) {
        return request.post(`/api/workflows/projects/${projectId}/discover`, null, {
            params: { max_results: maxResults }
        })
    },

    // 文献分析
    async startAnalysis(projectId, maxPapers = 20) {
        return request.post(`/api/workflows/projects/${projectId}/analyze`, null, {
            params: { max_papers: maxPapers }
        })
    },

    // 脉络分析
    async startLandscape(projectId) {
        return request.post(`/api/workflows/projects/${projectId}/landscape`)
    },

    // 想法生成
    async startIdeas(projectId, numIdeas = 5) {
        return request.post(`/api/workflows/projects/${projectId}/ideas`, null, {
            params: { num_ideas: numIdeas }
        })
    },

    // 获取项目状态
    async getStatus(projectId) {
        return request.get(`/api/workflows/projects/${projectId}/status`)
    }
}

export const tasksApi = {
    async getTask(taskId) {
        return request.get(`/api/tasks/${taskId}`)
    },

    async listTasks() {
        return request.get('/api/tasks')
    },

    async cancelTask(taskId) {
        return request.delete(`/api/tasks/${taskId}`)
    }
}
