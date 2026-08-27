<template>
  <router-view />
</template>

<style>
:root {
  /* Element Plus 主题色：Trust Blue */
  --el-color-primary: #2563eb;
  --el-color-primary-light-3: #5b8def;
  --el-color-primary-light-5: #8fb4f5;
  --el-color-primary-light-7: #c3d7fa;
  --el-color-primary-light-8: #dde9fd;
  --el-color-primary-light-9: #eef4fe;
  --el-color-primary-dark-2: #1d4fd8;

  --el-border-radius-base: 8px;
  --el-border-radius-small: 6px;
  --el-border-radius-round: 999px;

  --app-font: 'Inter', 'HarmonyOS Sans SC', 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--app-font);
  background: #f5f7fb;
  color: #1e293b;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 全局滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Element Plus 卡片统一观感 */
.el-card {
  border: none;
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 6px 24px rgba(15, 23, 42, 0.05);
}
.el-card__header {
  border-bottom: 1px solid #eef2f7;
  font-weight: 600;
  color: #0f172a;
}

.el-button--primary {
  --el-button-hover-bg-color: #3b82f6;
  --el-button-hover-border-color: #3b82f6;
}

/* 页面通用页头 */
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}
.page-desc {
  margin-top: 4px;
  font-size: 13px;
  color: #64748b;
}
</style>
