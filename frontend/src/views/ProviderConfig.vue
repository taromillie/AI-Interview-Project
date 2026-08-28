<template>
  <div class="provider-page">
    <div class="page-banner">
      <div class="banner-left">
        <div class="banner-icon">
          <el-icon :size="24"><Setting /></el-icon>
        </div>
        <div>
          <div class="banner-title">模型配置</div>
          <div class="banner-desc">API Key 加密存储，仅用于调用大模型。支持 DeepSeek / Kimi / GLM / Qwen / OpenAI 等兼容接口。</div>
        </div>
      </div>
    </div>
    <el-card>
      <template #header>
        <span>模型配置（LLM Provider）</span>
        <el-tag v-if="active && active.configured" type="success" class="active-tag">
          {{ active.provider_name }} · {{ active.model }}
        </el-tag>
      </template>

    <el-form :model="form" label-width="100px" class="form">
      <el-form-item label="供应商">
        <el-select v-model="form.provider_name" placeholder="选择供应商" @change="onProviderChange">
          <el-option v-for="(url, name) in KNOWN_PROVIDERS" :key="name" :label="name" :value="name" />
          <el-option label="自定义 (OpenAI 兼容)" value="custom" />
        </el-select>
      </el-form-item>

      <el-form-item v-if="form.provider_name === 'custom'" label="Base URL">
        <el-input v-model="form.base_url" placeholder="https://your-api.example.com/v1" />
      </el-form-item>

      <el-form-item label="模型">
        <el-input v-model="form.model" :placeholder="defaultModel" />
      </el-form-item>

      <el-form-item label="API Key">
        <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="saving" @click="save">保存并设为当前</el-button>
      </el-form-item>
    </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { Setting } from '@element-plus/icons-vue'
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

const KNOWN_PROVIDERS = {
  deepseek: 'https://api.deepseek.com/v1',
  kimi: 'https://api.moonshot.cn/v1',
  glm: 'https://open.bigmodel.cn/api/paas/v4',
  qwen: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  openai: 'https://api.openai.com/v1',
}

const DEFAULT_MODELS = {
  deepseek: 'deepseek-chat',
  kimi: 'moonshot-v1-8k',
  glm: 'glm-4-flash',
  qwen: 'qwen-plus',
  openai: 'gpt-4o-mini',
}

const form = reactive({
  provider_name: 'deepseek',
  base_url: '',
  model: '',
  api_key: '',
})

const active = ref(null)
const saving = ref(false)

const defaultModel = () => DEFAULT_MODELS[form.provider_name] || ''

function onProviderChange(name) {
  form.base_url = name === 'custom' ? '' : KNOWN_PROVIDERS[name]
  form.model = DEFAULT_MODELS[name] || ''
}

async function loadActive() {
  try {
    active.value = await http.get('/providers/active')
  } catch {
    /* 忽略 */
  }
}

async function save() {
  if (!form.api_key) {
    ElMessage.warning('请填写 API Key')
    return
  }
  const payload = {
    provider_name: form.provider_name,
    api_key: form.api_key,
    base_url: form.base_url || undefined,
    model: form.model || DEFAULT_MODELS[form.provider_name],
  }
  saving.value = true
  try {
    await http.post('/providers', payload)
    ElMessage.success('已保存并设为当前模型')
    await loadActive()
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadActive()
  onProviderChange('deepseek')
})
</script>

<style scoped>
.active-tag {
  margin-left: 12px;
}


.form {
  max-width: 560px;
}
</style>
