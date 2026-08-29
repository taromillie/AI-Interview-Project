<template>
  <router-view />
</template>

<style>
:root {
  /* Element Plus 主题色：靛蓝品牌色 #6366F1 */
  --el-color-primary: #6366f1;
  --el-color-primary-light-3: #8b8df4;
  --el-color-primary-light-5: #aeb0f8;
  --el-color-primary-light-7: #d1d2fb;
  --el-color-primary-light-8: #e3e4fd;
  --el-color-primary-light-9: #f1f1fe;
  --el-color-primary-dark-2: #4f46e5;

  --el-border-radius-base: 12px;
  --el-border-radius-small: 10px;
  --el-border-radius-round: 999px;

  /* ── 设计令牌：奶油米色 + 毛玻璃玻璃态（严格对标参考图） ── */
  --bg-soft: #f7f3ea;
  --primary: #6366f1;
  --secondary: #8b5cf6;
  --text-main: #1e293b;
  --text-sub: #64748b;
  --shadow-glass: 0 12px 28px rgba(99, 102, 241, 0.12);
  --border-glass: rgba(255, 255, 255, 0.85);

  --app-bg: var(--bg-soft);
  --app-text: var(--text-main);
  --app-text-secondary: var(--text-sub);
  --app-text-muted: #94a3b8;
  --app-border: rgba(255, 255, 255, 0.85);
  --app-border-strong: rgba(99, 102, 241, 0.24);
  --app-brand: var(--primary);
  --app-brand-dark: #4f46e5;
  --app-brand-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  --app-brand-soft: rgba(99, 102, 241, 0.1);
  --app-success: #10b981;
  --app-warning: #f59e0b;
  --app-danger: #ef4444;

  /* 毛玻璃玻璃面板令牌 */
  --glass-bg: rgba(255, 255, 255, 0.72);
  --glass-bg-strong: rgba(255, 255, 255, 0.86);
  --glass-border: rgba(255, 255, 255, 0.85);
  --glass-blur: 20px;

  --app-shadow-sm: 0 6px 18px rgba(99, 102, 241, 0.08);
  --app-shadow-md: var(--shadow-glass);
  --app-radius-lg: 24px;
  --app-radius-md: 18px;

  /* 自定义缓动曲线 */
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
  --ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);

  /* ── 动效令牌（transitions.dev 共享刻度） ── */
  --duration-stagger: 40ms;
  --duration-micro: 80ms;
  --duration-quick: 150ms;
  --duration-fast: 250ms;
  --duration-medium: 350ms;
  --duration-slow: 400ms;
  --duration-very-slow: 500ms;
  --ease-smooth-out: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-linear: linear;
  --ease-bounce: cubic-bezier(0.34, 1.36, 0.64, 1);
  --ease-bounce-strong: cubic-bezier(0.34, 3.85, 0.64, 1);
  --distance-micro: 4px;
  --distance-small: 6px;
  --distance-base: 8px;
  --distance-medium: 12px;
  --distance-large: 30px;
  --scale-large: 0.96;
  --scale-medium: 0.97;
  --scale-small: 0.98;
  --scale-tiny: 0.99;
  --blur-small: 2px;
  --blur-medium: 3px;
  --blur-large: 8px;

  --app-font: -apple-system, BlinkMacSystemFont, 'Inter', 'HarmonyOS Sans SC', 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  height: 100%;
}

body {
  font-family: var(--app-font);
  background: linear-gradient(135deg, #f7f3ea 0%, #efebe1 100%);
  background-attachment: fixed;
  position: relative;
  overflow-x: hidden;
  color: var(--app-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
/* 弥散光斑（固定，位于内容之下） */
body::before {
  content: "";
  position: fixed;
  width: 460px;
  height: 460px;
  border-radius: 50%;
  background: rgba(139, 92, 246, 0.1);
  filter: blur(90px);
  top: 6%;
  right: 4%;
  z-index: 0;
  pointer-events: none;
}
body::after {
  content: "";
  position: fixed;
  width: 380px;
  height: 380px;
  border-radius: 50%;
  background: rgba(99, 102, 241, 0.09);
  filter: blur(80px);
  bottom: 10%;
  left: 6%;
  z-index: 0;
  pointer-events: none;
}
#app {
  position: relative;
  z-index: 1;
}

/* ==================== 毛玻璃玻璃态工具类 ==================== */
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-glass);
  box-shadow: var(--shadow-glass);
  border-radius: var(--app-radius-lg);
  transition: transform 0.28s var(--ease-out), box-shadow 0.28s var(--ease-out);
}
.glass-card--hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 36px rgba(99, 102, 241, 0.16);
}
.dialog-glass {
  background: var(--glass-bg-strong);
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  border: 1px solid var(--border-glass);
  border-radius: 24px;
  box-shadow: var(--shadow-glass);
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
  background: #d4d4d4;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #999999;
}

/* ==================== Element Plus 细节统一 ==================== */

/* 卡片：毛玻璃面板 */
.el-card {
  border: 1px solid var(--glass-border);
  border-radius: var(--app-radius-md);
  background: var(--glass-bg-strong);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  box-shadow: var(--app-shadow-sm);
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}
.el-card__header {
  border-bottom: 1px solid var(--app-border);
  font-weight: 600;
  color: var(--app-text);
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.el-card__header .el-button {
  flex-shrink: 0;
}

/* 按钮按压反馈：任何可点击按钮都应给出即时反馈 */
.el-button {
  transition: transform 160ms var(--ease-out), background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}
.el-button:active:not(.is-disabled) {
  transform: scale(0.97);
}

/* 主按钮：纯墨色，去渐变 */
.el-button--primary {
  --el-button-hover-bg-color: #333333;
  --el-button-hover-border-color: #333333;
  --el-button-active-bg-color: #000000;
  --el-button-active-border-color: #000000;
}
.el-button--primary:not(.is-plain):not(.is-text) {
  background-color: #1a1a1a;
  background-image: none;
  border: none;
  box-shadow: 0 2px 8px rgba(26, 26, 26, 0.18);
}
.el-button--primary:not(.is-plain):not(.is-text):hover {
  background-color: #333333;
  box-shadow: 0 4px 12px rgba(26, 26, 26, 0.22);
}
.el-button--primary.is-plain {
  --el-button-plain-hover-bg-color: var(--app-brand-soft);
}

/* 表单输入圆角统一 */
.el-input__wrapper,
.el-textarea__inner,
.el-select__wrapper {
  border-radius: 8px;
}
.el-textarea__inner {
  font-family: var(--app-font);
}

/* 对话框圆角 */
.el-dialog {
  border-radius: var(--app-radius-lg);
  overflow: hidden;
}
.el-dialog__header {
  padding: 20px 24px 8px;
}
.el-dialog__body {
  padding: 12px 24px 8px;
}
.el-dialog__footer {
  padding: 12px 24px 20px;
}

/* 模态框打开/关闭过渡：scale + fade */
.el-overlay-dialog {
  transition: opacity 0.25s var(--ease-smooth-out);
}
.el-overlay-dialog .el-dialog {
  transform-origin: center;
  transition: transform 0.25s var(--ease-smooth-out), opacity 0.25s var(--ease-smooth-out);
}
.el-overlay.is-message-box .el-message-box,
.el-overlay.is-message-box {
  transition: opacity 0.25s var(--ease-smooth-out);
}
.el-overlay.is-message-box .el-message-box {
  transform-origin: center;
  transition: transform 0.25s var(--ease-smooth-out), opacity 0.25s var(--ease-smooth-out);
}
.dialog-fade-enter-from .el-dialog,
.dialog-fade-leave-to .el-dialog {
  transform: scale(0.96) translateY(8px);
  opacity: 0;
}
.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}
.message-box-fade-enter-from .el-message-box,
.message-box-fade-leave-to .el-message-box {
  transform: scale(0.96);
  opacity: 0;
}
.message-box-fade-enter-from,
.message-box-fade-leave-to {
  opacity: 0;
}

/* 消息提示过渡 */
.el-message {
  transition: transform 0.25s var(--ease-smooth-out), opacity 0.25s var(--ease-smooth-out) !important;
}
.el-message-fade-enter-from,
.el-message-fade-leave-to {
  transform: translateY(8px) scale(0.97);
  opacity: 0;
}

/* 表格细节 */
.el-table {
  --el-table-header-bg-color: #fafaf9;
  --el-table-header-text-color: #666666;
  --el-table-border-color: #ededed;
  --el-table-row-hover-bg-color: #fafaf9;
  border-radius: 10px;
}
.el-table th.el-table__cell {
  font-weight: 600;
}

/* 分隔线配色 */
.el-divider__text {
  font-weight: 600;
  font-size: 13px;
  color: var(--app-text);
  background: transparent;
}

/* Timeline 圆点 */
.el-timeline-item__tail {
  border-left: 2px solid #ededed;
}
.el-timeline-item__node {
  box-shadow: 0 0 0 4px rgba(26, 26, 26, 0.08);
}

/* 提示消息 */
.el-message {
  border-radius: 10px;
  box-shadow: var(--app-shadow-md);
}

/* ==================== 通用页面元素 ==================== */

/* 页头 Banner（白色卡片 + 深色文字，兼容所有背景） */
.page-banner {
  position: relative;
  overflow: hidden;
  border-radius: var(--app-radius-lg);
  padding: 22px 26px;
  margin-bottom: 20px;
  color: var(--app-text);
  background: var(--glass-bg-strong);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  box-shadow: var(--app-shadow-sm);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.banner-left {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  z-index: 1;
}
.banner-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: var(--app-brand-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
  color: var(--app-brand);
}
.banner-title {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.2px;
}
.banner-desc {
  margin-top: 5px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--app-text-secondary);
  max-width: 720px;
}
.banner-actions {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

/* 轻量页头（纯色卡片） */
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--app-text);
}
.page-desc {
  margin-top: 4px;
  font-size: 13px;
  color: var(--app-text-secondary);
}

/* 小节标题（左竖条装饰） */
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
  margin: 20px 0 12px;
}
.section-title::before {
  content: '';
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--app-brand);
}

/* 历史列表条目统一 */
.history-list {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}
.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--app-border);
  border-radius: 10px;
  cursor: pointer;
  transition: transform 160ms var(--ease-out), border-color 0.2s ease, background-color 0.2s ease;
}
.history-item:active {
  transform: scale(0.98);
}
@media (hover: hover) and (pointer: fine) {
  .history-item:hover {
    border-color: var(--app-border-strong);
    background: #fafaf9;
  }
}
.history-item.selected {
  border-color: var(--app-success);
  background: #eef7f2;
}
.history-item.active {
  border-color: var(--app-brand);
  background: var(--app-brand-soft);
}

/* 空状态插画色 */
.el-empty__description p {
  color: var(--app-text-muted);
}

/* 卡片内图标徽章 */
.icon-badge {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
  flex-shrink: 0;
}

/* 页面进入动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 尊重系统「减少动态效果」偏好 */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
</style>
