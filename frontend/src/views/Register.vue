<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
    <n-card class="w-full max-w-md" :bordered="false">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-white mb-2">🔬 AI-Researcher</h1>
        <p class="text-gray-400">创建您的账号</p>
      </div>
      
      <n-form ref="formRef" :model="formData" :rules="rules">
        <n-form-item path="email" label="邮箱">
          <n-input v-model:value="formData.email" placeholder="请输入邮箱" size="large" />
        </n-form-item>
        
        <n-form-item path="username" label="用户名">
          <n-input v-model:value="formData.username" placeholder="请输入用户名" size="large" />
        </n-form-item>
        
        <n-form-item path="password" label="密码">
          <n-input 
            v-model:value="formData.password" 
            type="password" 
            placeholder="请设置密码"
            size="large"
            show-password-on="click"
          />
        </n-form-item>
        
        <n-button 
          type="primary" 
          block 
          size="large"
          :loading="loading"
          @click="handleRegister"
        >
          注册
        </n-button>
      </n-form>
      
      <div class="mt-6 text-center">
        <span class="text-gray-400">已有账号？</span>
        <router-link to="/login" class="text-blue-400 hover:text-blue-300 ml-2">
          立即登录
        </router-link>
      </div>
    </n-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)
const formData = ref({
  email: '',
  username: '',
  password: ''
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

async function handleRegister() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  
  loading.value = true
  const result = await authStore.register(
    formData.value.email, 
    formData.value.username, 
    formData.value.password
  )
  loading.value = false
  
  if (result.success) {
    message.success('注册成功，请登录')
    router.push('/login')
  } else {
    message.error(result.error)
  }
}
</script>
