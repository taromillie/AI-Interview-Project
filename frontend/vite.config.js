import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
    // 保留符号链接路径（C 盘 junction → F 盘真实路径），
    // 避免 Vite realpath 后对中文路径生成乱码的 /@fs/ URL
    preserveSymlinks: true,
  },
  build: {
    rollupOptions: {
      // 使用相对路径作为入口，规避 Windows 中文路径下
      // rollup emitFile 校验把绝对路径当作 fileName 的缺陷
      input: 'index.html',
    },
  },
  server: {
    port: 5173,
    // 本项目位于 CodeBuddy 工作区，目录 C:\Users\Meng\CodeBuddy\ai模拟面试
    // 实际是 junction，物理文件在 F:\CodeBuddyStorage\CodeBuddy-Projects\ai模拟面试。
    // Vite 的 server.fs 默认只允许访问 root 内文件，物理路径在 root 之外，
    // 导致模块解析失败（Failed to load url ... resolved id: F:/...）。此处放开限制。
    fs: {
      strict: false,
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
