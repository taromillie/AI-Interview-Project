import { createApp } from 'vue'
import { createPinia } from 'pinia'
import * as Icons from '@element-plus/icons-vue'

// Element Plus 命令式组件：模板中的 el-* 组件由 unplugin-vue-components
// 按需自动导入（组件 + 样式），此处仅手动注册命令式 API 及其样式。
import { ElLoading, ElMessage, ElMessageBox } from 'element-plus'
import 'element-plus/es/components/loading/style/css'
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(ElLoading)
app.use(ElMessage)
app.use(ElMessageBox)

// 仅注册各页面实际使用的图标（从模板中统计，替代全量注册以减小包体）
const iconNames = [
  'Aim', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Bell', 'BellFilled', 'Calendar',
  'ChatDotSquare', 'Check', 'CircleCheckFilled', 'Clock', 'Close', 'Collection',
  'Compass', 'DataAnalysis', 'Document', 'FolderOpened', 'Grid', 'InfoFilled',
  'Link', 'Location', 'MagicStick', 'Microphone', 'Money', 'Odometer',
  'OfficeBuilding', 'Plus', 'Pointer', 'Position', 'Promotion', 'Refresh',
  'RefreshLeft', 'RefreshRight', 'Right', 'Search', 'Setting', 'TrendCharts',
  'Trophy', 'UploadFilled', 'User', 'VideoCamera', 'Wallet', 'Warning',
  'WarningFilled',
]
for (const name of iconNames) {
  app.component(name, Icons[name])
}

app.use(createPinia())
app.use(router)

// 全局兜底：渲染/异步异常不再静默白屏，统一提示并留痕
let lastErrorAt = 0
function reportGlobalError(err) {
  console.error('[App] unhandled error:', err)
  const now = Date.now()
  if (now - lastErrorAt < 2000) return
  lastErrorAt = now
  ElMessage.error('页面发生异常，请刷新重试')
}
app.config.errorHandler = (err) => reportGlobalError(err)
window.addEventListener('unhandledrejection', (e) => reportGlobalError(e.reason))

app.mount('#app')
