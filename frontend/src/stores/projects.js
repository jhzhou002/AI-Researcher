import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectsApi } from '../api/projects'

export const useProjectsStore = defineStore('projects', () => {
    const projects = ref([])
    const currentProject = ref(null)
    const loading = ref(false)

    async function fetchProjects() {
        loading.value = true
        try {
            const data = await projectsApi.list()
            // 后端返回 {projects: [...], total: number}
            projects.value = data.projects || []
        } catch (error) {
            console.error('Failed to fetch projects:', error)
            projects.value = []
        } finally {
            loading.value = false
        }
    }

    async function fetchProject(id) {
        loading.value = true
        try {
            const data = await projectsApi.get(id)
            currentProject.value = data
            return data
        } catch (error) {
            console.error('Failed to fetch project:', error)
            return null
        } finally {
            loading.value = false
        }
    }

    async function createProject(projectData) {
        try {
            const newProject = await projectsApi.create(projectData)
            // 确保 projects 是数组
            if (Array.isArray(projects.value)) {
                projects.value.unshift(newProject) // 新项目放在最前面
            }
            return { success: true, project: newProject }
        } catch (error) {
            console.error('Failed to create project:', error)
            return { success: false, error: error.response?.data?.detail || 'Creation failed' }
        }
    }

    async function deleteProject(id) {
        try {
            await projectsApi.delete(id)
            projects.value = projects.value.filter(p => p.id !== id)
            return { success: true }
        } catch (error) {
            return { success: false, error: error.response?.data?.detail || 'Deletion failed' }
        }
    }

    return {
        projects,
        currentProject,
        loading,
        fetchProjects,
        fetchProject,
        createProject,
        deleteProject
    }
})
