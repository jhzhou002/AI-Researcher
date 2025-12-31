<template>
  <div class="min-h-screen bg-gray-900">
    <!-- Header -->
    <header class="bg-gray-800 border-b border-gray-700">
      <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <h1 class="text-2xl font-bold text-white">🔬 AI-Researcher</h1>
        <div class="flex items-center gap-4">
          <span class="text-gray-400">{{ authStore.user?.username }}</span>
          <n-button quaternary @click="handleLogout">退出</n-button>
        </div>
      </div>
    </header>
    
    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 py-8">
      <div class="flex justify-between items-center mb-8">
        <h2 class="text-3xl font-bold text-white">我的研究项目</h2>
        <n-button type="primary" size="large" @click="showCreateModal = true">
          + 创建项目
        </n-button>
      </div>
      
      <!-- Loading -->
      <div v-if="projectsStore.loading" class="text-center py-16">
        <n-spin size="large" />
        <p class="text-gray-400 mt-4">加载中...</p>
      </div>
      
      <!-- Empty State -->
      <div v-else-if="projectsStore.projects.length === 0" class="text-center py-16">
        <div class="text-6xl mb-4">📚</div>
        <p class="text-gray-400 text-lg">还没有研究项目</p>
        <p class="text-gray-500">点击上方按钮创建您的第一个项目</p>
      </div>
      
      <!-- Projects Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <n-card 
          v-for="project in projectsStore.projects" 
          :key="project.id"
          hoverable
          class="cursor-pointer bg-gray-800 border-gray-700"
          @click="goToProject(project.id)"
        >
          <div class="flex justify-between items-start mb-4">
            <h3 class="text-xl font-semibold text-white">{{ project.title }}</h3>
            <n-tag :type="getStepTagType(project.current_step)">
              {{ getStepLabel(project.current_step) }}
            </n-tag>
          </div>
          
          <p class="text-gray-400 mb-4">
            <span class="text-blue-400">{{ project.keywords }}</span>
          </p>
          
          <div class="flex justify-between text-sm text-gray-500">
            <span>{{ project.year_start }} - {{ project.year_end }}</span>
            <span>{{ formatDate(project.created_at) }}</span>
          </div>
        </n-card>
      </div>
    </main>
    
    <!-- Create Project Modal -->
    <n-modal v-model:show="showCreateModal" preset="card" title="创建研究项目" style="width: 600px;">
      <n-form ref="createFormRef" :model="createForm" :rules="createRules">
        <n-form-item label="项目标题" path="title">
          <n-input v-model:value="createForm.title" placeholder="如：大语言模型Agent规划能力研究" />
        </n-form-item>
        
        <n-form-item label="研究关键词" path="keywords">
          <n-input v-model:value="createForm.keywords" placeholder="如：LLM agent planning reasoning" />
        </n-form-item>
        
        <n-grid :cols="2" :x-gap="16">
          <n-grid-item>
            <n-form-item label="起始年份" path="year_start">
              <n-input-number v-model:value="createForm.year_start" :min="2000" :max="2025" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="结束年份" path="year_end">
              <n-input-number v-model:value="createForm.year_end" :min="2000" :max="2025" />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        
        <n-grid :cols="3" :x-gap="16">
          <n-grid-item>
            <n-form-item label="期刊等级">
              <n-select v-model:value="createForm.journal_level" :options="journalOptions" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="论文类型">
              <n-select v-model:value="createForm.paper_type" :options="paperTypeOptions" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="研究领域">
              <n-select v-model:value="createForm.field" :options="fieldOptions" />
            </n-form-item>
          </n-grid-item>
        </n-grid>
      </n-form>
      
      <template #footer>
        <div class="flex justify-end gap-3">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" :loading="creating" @click="handleCreate">创建</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { useProjectsStore } from '../stores/projects'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const projectsStore = useProjectsStore()

const showCreateModal = ref(false)
const creating = ref(false)
const createFormRef = ref(null)

const createForm = ref({
  title: '',
  keywords: '',
  year_start: 2023,
  year_end: 2024,
  journal_level: 'any',
  paper_type: 'research',
  field: 'any'
})

const createRules = {
  title: { required: true, message: '请输入项目标题' },
  keywords: { required: true, message: '请输入研究关键词' }
}

const journalOptions = [
  { label: '不限', value: 'any' },
  { label: '顶级', value: 'top' },
  { label: '一区', value: 'q1' },
  { label: '二区', value: 'q2' }
]

const paperTypeOptions = [
  { label: '不限', value: 'any' },
  { label: '原创研究', value: 'research' },
  { label: '综述', value: 'survey' }
]

const fieldOptions = [
  { label: '不限', value: 'any' },
  { label: 'NLP', value: 'nlp' },
  { label: 'CV', value: 'cv' },
  { label: 'ML', value: 'ml' },
  { label: 'Systems', value: 'systems' }
]

function getStepLabel(step) {
  const labels = {
    'init': '未开始',
    'discovery': '已检索',
    'analysis': '已分析',
    'landscape': '已梳理',
    'ideas': '已生成想法',
    'method': '已设计方法',
    'draft': '已生成草稿'
  }
  return labels[step] || '未开始'
}

function getStepTagType(step) {
  const types = {
    'init': 'default',
    'discovery': 'info',
    'analysis': 'warning',
    'landscape': 'success',
    'ideas': 'success',
    'method': 'success',
    'draft': 'success'
  }
  return types[step] || 'default'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function goToProject(id) {
  router.push(`/project/${id}`)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

async function handleCreate() {
  try {
    await createFormRef.value?.validate()
  } catch {
    return
  }
  
  creating.value = true
  const result = await projectsStore.createProject(createForm.value)
  creating.value = false
  
  if (result.success) {
    message.success('项目创建成功!')
    showCreateModal.value = false
    // 重置表单
    createForm.value = {
      title: '',
      keywords: '',
      year_start: 2023,
      year_end: 2024,
      journal_level: 'any',
      paper_type: 'research',
      field: 'any'
    }
    // 跳转到项目详情
    router.push(`/project/${result.project.id}`)
  } else {
    message.error(result.error)
  }
}

onMounted(async () => {
  await authStore.fetchUser()
  await projectsStore.fetchProjects()
})
</script>
