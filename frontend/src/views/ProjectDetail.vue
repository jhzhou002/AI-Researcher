<template>
  <div class="min-h-screen bg-gray-900">
    <!-- Header -->
    <header class="bg-gray-800 border-b border-gray-700">
      <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <div class="flex items-center gap-4">
          <router-link to="/projects" class="text-gray-400 hover:text-white">
            ← 返回
          </router-link>
          <h1 class="text-xl font-bold text-white">{{ project?.title }}</h1>
        </div>
        <n-tag :type="getStepTagType(project?.current_step)">
          {{ getStepLabel(project?.current_step) }}
        </n-tag>
      </div>
    </header>
    
    <main class="max-w-7xl mx-auto px-4 py-8">
      <!-- Loading -->
      <div v-if="loading" class="text-center py-16">
        <n-spin size="large" />
      </div>
      
      <template v-else-if="project">
        <!-- Workflow Steps -->
        <n-card class="mb-8 bg-gray-800 border-gray-700">
          <h2 class="text-xl font-bold text-white mb-6">研究流程</h2>
          
          <n-steps :current="currentStep" class="mb-6">
            <n-step title="文献检索" description="检索相关论文" />
            <n-step title="文献分析" description="分析论文内容" />
            <n-step title="脉络梳理" description="研究脉络分析" />
            <n-step title="想法生成" description="生成研究想法" />
          </n-steps>
          
          <!-- Action Buttons -->
          <div class="flex flex-wrap gap-4">
            <n-button 
              type="primary" 
              :disabled="currentStep !== 1 || runningTask !== null"
              :loading="runningTask === 'discover'"
              @click="startTask('discover')"
            >
              🔍 开始检索
            </n-button>
            
            <n-button 
              type="info" 
              :disabled="currentStep !== 2 || runningTask !== null"
              :loading="runningTask === 'analyze'"
              @click="startTask('analyze')"
            >
              📖 分析文献
            </n-button>
            
            <n-button 
              type="warning" 
              :disabled="currentStep !== 3 || runningTask !== null"
              :loading="runningTask === 'landscape'"
              @click="startTask('landscape')"
            >
              🗺️ 脉络分析
            </n-button>
            
            <n-button 
              type="success" 
              :disabled="currentStep !== 4 || runningTask !== null"
              :loading="runningTask === 'ideas'"
              @click="startTask('ideas')"
            >
              💡 生成想法
            </n-button>
          </div>
        </n-card>
        
        <!-- Task Progress -->
        <n-card v-if="currentTask" class="mb-8 bg-gray-800 border-gray-700">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">{{ currentTask.task_name }}</h3>
            <n-tag :type="getTaskStatusType(currentTask.status)">
              {{ currentTask.status }}
            </n-tag>
          </div>
          
          <n-progress 
            type="line" 
            :percentage="currentTask.progress" 
            :status="getProgressStatus(currentTask.status)"
            :show-indicator="true"
          />
          
          <p v-if="currentTask.result?.current_message" class="text-gray-400 mt-4">
            {{ currentTask.result.current_message }}
          </p>
        </n-card>
        
        <!-- Results -->
        <n-card class="bg-gray-800 border-gray-700">
          <n-tabs type="line" animated>
            <!-- Papers Tab -->
            <n-tab-pane name="papers" tab="📄 论文列表">
              <div class="flex justify-between items-center mb-4">
                 <span class="text-gray-400 text-sm">共 {{ papers.length }} 篇文献</span>
                 <n-button 
                    size="small" 
                    secondary 
                    type="primary" 
                    @click="downloadFile('papers', 'excel')" 
                    :disabled="papers.length === 0"
                 >
                    📥 导出 Excel
                 </n-button>
              </div>

              <div v-if="papers.length === 0" class="text-center py-8 text-gray-400">
                暂无论文，请先运行文献检索
              </div>
              <div v-else class="space-y-4">
                <div 
                  v-for="paper in papers" 
                  :key="paper.id"
                  class="p-4 bg-gray-700 rounded-lg"
                >
                  <div class="flex justify-between items-start mb-2">
                    <h4 class="text-white font-medium">{{ paper.title }}</h4>
                    <n-tag size="small" type="info">
                      相关度: {{ (paper.relevance_score * 100).toFixed(0) }}%
                    </n-tag>
                  </div>
                  <p class="text-gray-400 text-sm line-clamp-2 my-2">{{ paper.abstract }}</p>
                  <div class="mt-2 text-xs text-gray-500 flex justify-between items-center">
                    <span>{{ paper.published }} | {{ paper.authors?.slice(0, 3).join(', ') }}</span>
                    <div class="flex gap-2">
                       <n-tag v-if="paper.partition" size="small" :type="paper.partition === 'CCF-A' ? 'error' : 'success'" ghost>
                        {{ paper.partition }}
                      </n-tag>
                      <n-tag v-if="paper.journal" size="small" type="warning" ghost>
                        {{ paper.journal }}
                      </n-tag>
                    </div>
                  </div>
                </div>
              </div>
            </n-tab-pane>
            
            <!-- Ideas Tab -->
            <n-tab-pane name="ideas" tab="💡 研究想法">
              <div class="flex justify-between items-center mb-4">
                 <span class="text-gray-400 text-sm">共 {{ ideas.length }} 个想法</span>
                 <n-dropdown :options="exportOptions" @select="handleExportSelect">
                   <n-button 
                      size="small" 
                      secondary 
                      type="primary"
                      :disabled="ideas.length === 0"
                   >
                      📥 导出
                   </n-button>
                 </n-dropdown>
              </div>

              <div v-if="ideas.length === 0" class="text-center py-8 text-gray-400">
                暂无想法，请完成前序步骤后生成
              </div>
              <div v-else class="space-y-4">
                <div 
                  v-for="idea in ideas" 
                  :key="idea.id"
                  class="p-4 bg-gray-700 rounded-lg"
                >
                  <h4 class="text-white font-medium mb-2">{{ idea.title }}</h4>
                  <p class="text-gray-400 text-sm mb-3">{{ idea.motivation }}</p>
                  <div class="flex gap-4 text-sm">
                    <span class="text-green-400">
                      新颖性: {{ (idea.novelty_score * 100).toFixed(0) }}%
                    </span>
                    <span class="text-blue-400">
                      可行性: {{ (idea.feasibility_score * 100).toFixed(0) }}%
                    </span>
                  </div>
                </div>
              </div>
            </n-tab-pane>
          </n-tabs>
        </n-card>
      </template>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useProjectsStore } from '../stores/projects'
import { projectsApi } from '../api/projects'
import { workflowsApi, tasksApi } from '../api/workflows'

const route = useRoute()
const message = useMessage()
const projectsStore = useProjectsStore()

const loading = ref(true)
const project = ref(null)
const papers = ref([])
const ideas = ref([])
const currentTask = ref(null)
const runningTask = ref(null)
let pollInterval = null

const exportOptions = [
  { label: '导出 Excel', key: 'excel' },
  { label: '导出 Markdown', key: 'markdown' }
]

function handleExportSelect(key) {
  downloadFile('ideas', key)
}

const currentStep = computed(() => {
  if (!project.value?.current_step) return 0
  
  const status = project.value.current_step.toString().toLowerCase().trim()
  
  const steps = { 
    'intent': 1, 
    'init': 0, 
    'discovery': 2, 
    'analysis': 3, 
    'landscape': 4, 
    'ideas': 5,
    'completed': 6
  }
  
  return steps[status] !== undefined ? steps[status] : 1
})

function getStepLabel(step) {
  const labels = {
    'intent': '未开始',
    'init': '未开始',
    'discovery': '已检索',
    'analysis': '已分析',
    'landscape': '已梳理',
    'ideas': '已生成想法'
  }
  return labels[step] || '未开始'
}

function getStepTagType(step) {
  const types = {
    'intent': 'default',
    'init': 'default',
    'discovery': 'info',
    'analysis': 'warning',
    'landscape': 'success',
    'ideas': 'success'
  }
  return types[step] || 'default'
}

function getTaskStatusType(status) {
  const types = {
    'pending': 'default',
    'running': 'warning',
    'completed': 'success',
    'failed': 'error'
  }
  return types[status] || 'default'
}

function getProgressStatus(status) {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'error'
  return 'default'
}

async function loadProject() {
  loading.value = true
  const projectId = route.params.id
  
  project.value = await projectsStore.fetchProject(projectId)
  
  // 加载论文和想法
  try {
    papers.value = await projectsApi.getPapers(projectId)
  } catch (e) {
    papers.value = []
  }
  
  try {
    ideas.value = await projectsApi.getIdeas(projectId)
  } catch (e) {
    ideas.value = []
  }
  
  loading.value = false
}

async function startTask(taskType) {
  const projectId = route.params.id
  runningTask.value = taskType
  
  try {
    let task
    switch (taskType) {
      case 'discover':
        task = await workflowsApi.startDiscovery(projectId, 30)
        break
      case 'analyze':
        task = await workflowsApi.startAnalysis(projectId, 20)
        break
      case 'landscape':
        task = await workflowsApi.startLandscape(projectId)
        break
      case 'ideas':
        task = await workflowsApi.startIdeas(projectId, 5)
        break
    }
    
    currentTask.value = task
    message.info(`任务已启动: ${task.task_name}`)
    
    // 开始轮询
    startPolling(task.task_id)
  } catch (error) {
    message.error(error.response?.data?.detail || '任务启动失败')
    runningTask.value = null
  }
}

function startPolling(taskId) {
  if (pollInterval) clearInterval(pollInterval)
  
  pollInterval = setInterval(async () => {
    try {
      const task = await tasksApi.getTask(taskId)
      currentTask.value = task
      
      if (task.status === 'completed') {
        message.success('任务完成!')
        stopPolling()
        runningTask.value = null
        // 重新加载项目数据以获取新的papers/ideas
        await loadProject()
      } else if (task.status === 'failed') {
        message.error('任务失败: ' + (task.error_message || '未知错误'))
        stopPolling()
        runningTask.value = null
      }
    } catch (e) {
      console.error('Poll error:', e)
    }
  }, 2000)
}

async function downloadFile(type, format = 'excel') {
  try {
    const projectId = route.params.id
    let blob
    let filename
    
    message.loading('正在导出...', { duration: 0 })
    
    if (type === 'papers') {
      blob = await projectsApi.exportPapers(projectId)
      filename = `papers_project_${projectId}.xlsx`
    } else {
      blob = await projectsApi.exportIdeas(projectId, format)
      filename = `ideas_project_${projectId}.${format === 'excel' ? 'xlsx' : 'md'}`
    }
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    
    // Cleanup
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    message.destroyAll()
    message.success('导出成功')
  } catch (e) {
    message.destroyAll()
    console.error('Download error:', e)
    message.error('导出失败')
  }
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

onMounted(() => {
  loadProject()
})

onUnmounted(() => {
  stopPolling()
})
</script>
