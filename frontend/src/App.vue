<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup>
// 全局中文语言包（Element Plus 按需引入后由 ConfigProvider 接管 locale）
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>

<style>
/* 注意：Element Plus 按需引入的 base.css 含 :root 亮色变量（--el-fill-color-blank:#fff 等），
   路由懒加载时会在运行时后注入并覆盖 :root。用 html:root 提高特异性，保证主题变量始终生效 */
html:root {
  /* ===== Element Plus 主题色：青蓝液态玻璃 ===== */
  --el-color-primary: #5ad0e6;
  --el-color-primary-light-3: #7fdcec;
  --el-color-primary-light-5: #a6e7f2;
  --el-color-primary-light-7: #cdf2f8;
  --el-color-primary-light-8: #e0f7fb;
  --el-color-primary-light-9: rgba(90, 208, 230, 0.12);
  --el-color-primary-dark-2: #3bb6cf;

  --el-border-radius-base: 10px;
  --el-border-radius-small: 8px;
  --el-border-radius-round: 999px;

  /* ===== Element Plus 深色化（全局覆盖，使所有组件继承玻璃暗色） ===== */
  --el-bg-color: rgba(255, 255, 255, 0.04);
  --el-bg-color-page: transparent;
  --el-bg-color-overlay: #141b2e;
  --el-text-color-primary: #eaf0fb;
  --el-text-color-regular: #c4cde0;
  --el-text-color-secondary: #98a3bd;
  --el-text-color-placeholder: #6b7690;
  --el-text-color-disabled: #565f77;
  --el-border-color: rgba(255, 255, 255, 0.14);
  --el-border-color-light: rgba(255, 255, 255, 0.1);
  --el-border-color-lighter: rgba(255, 255, 255, 0.08);
  --el-border-color-extra-light: rgba(255, 255, 255, 0.06);
  --el-border-color-dark: rgba(255, 255, 255, 0.2);
  --el-border-color-hover: rgba(90, 208, 230, 0.5);
  --el-fill-color: rgba(255, 255, 255, 0.06);
  --el-fill-color-light: rgba(255, 255, 255, 0.05);
  --el-fill-color-lighter: rgba(255, 255, 255, 0.04);
  --el-fill-color-extra-light: rgba(255, 255, 255, 0.03);
  --el-fill-color-blank: transparent;
  --el-fill-color-dark: rgba(255, 255, 255, 0.08);
  --el-fill-color-darker: rgba(255, 255, 255, 0.1);
  --el-mask-color: rgba(8, 11, 20, 0.72);
  --el-disabled-bg-color: rgba(255, 255, 255, 0.04);
  --el-disabled-text-color: #565f77;
  --el-disabled-border-color: rgba(255, 255, 255, 0.1);

  /* ===== 设计令牌：深色液态玻璃 ===== */
  --app-bg: #080b14;
  --app-bg-deep: #05070e;
  --app-text: #eaf0fb;
  --app-text-secondary: #a6b0c8;
  --app-text-muted: #6f7a95;
  --app-border: rgba(255, 255, 255, 0.12);
  --app-border-strong: rgba(255, 255, 255, 0.22);

  --app-cyan: #5ad0e6;
  --app-blue: #6b8bff;
  --app-amber: #f2c14e;
  --app-brand: #5ad0e6;
  --app-brand-dark: #3bb6cf;
  --app-brand-gradient: linear-gradient(135deg, #5ad0e6 0%, #6b8bff 100%);
  --app-brand-soft: rgba(90, 208, 230, 0.14);
  --app-success: #43d9a3;
  --app-warning: #f2c14e;
  --app-danger: #ff6b7a;

  /* 玻璃表面 */
  --glass-bg: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.035));
  --glass-bg-strong: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.05));
  --glass-border: rgba(255, 255, 255, 0.14);
  --glass-blur: blur(24px) saturate(150%);
  --glass-highlight: inset 0 1px 0 0 rgba(255, 255, 255, 0.22);
  --glass-shadow: 0 20px 60px -22px rgba(0, 0, 0, 0.7), 0 8px 24px -14px rgba(0, 0, 0, 0.55);

  --app-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3), 0 8px 24px -14px rgba(0, 0, 0, 0.5);
  --app-shadow-md: 0 12px 40px -18px rgba(0, 0, 0, 0.65);
  --app-radius-lg: 18px;
  --app-radius-md: 14px;

  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
  --ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);

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
  color-scheme: dark;
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
  background: var(--app-bg);
  color: var(--app-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 全局滚动条 */
::-webkit-scrollbar {
  width: 9px;
  height: 9px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.16);
  border-radius: 5px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.28);
}

/* ==================== 液态玻璃通用工具类 ==================== */
.glass {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-highlight), var(--glass-shadow);
}
.glass-strong {
  background: var(--glass-bg-strong);
  backdrop-filter: blur(32px) saturate(160%);
  -webkit-backdrop-filter: blur(32px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.3), var(--glass-shadow);
}

/* 玻璃高光扫过 */
.glass-sheen {
  position: relative;
  overflow: hidden;
  isolation: isolate;
}
.glass-sheen::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(115deg, transparent 30%, rgba(255, 255, 255, 0.16) 48%, transparent 62%);
  transform: translateX(-120%);
  animation: glass-sheen 7s ease-in-out infinite;
  pointer-events: none;
  z-index: 1;
}
@keyframes glass-sheen {
  0%, 55% { transform: translateX(-120%); }
  75%, 100% { transform: translateX(120%); }
}

@keyframes app-blob {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(6%, -8%) scale(1.12); }
  66% { transform: translate(-7%, 5%) scale(0.94); }
}
@keyframes app-blob-2 {
  0%, 100% { transform: translate(0, 0) scale(1.05); }
  40% { transform: translate(-8%, 6%) scale(0.9); }
  70% { transform: translate(5%, 9%) scale(1.15); }
}
@keyframes app-rise {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.app-rise {
  opacity: 0;
  animation: app-rise 0.6s var(--ease-out) forwards;
}

/* ==================== Element Plus 深色玻璃细节 ==================== */

/* 卡片：玻璃（html 前缀提高特异性，防止被按需注入的组件样式覆盖） */
html .el-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--app-radius-md);
  box-shadow: var(--glass-highlight), var(--app-shadow-sm);
  color: var(--app-text);
  transition: border-color 0.25s ease, transform 0.25s var(--ease-out), box-shadow 0.25s ease;
}
html .el-card__header {
  border-bottom: 1px solid var(--app-border);
  font-weight: 600;
  color: var(--app-text);
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
html .el-card__body {
  color: var(--app-text-secondary);
}

/* 按钮按压反馈 */
.el-button {
  transition: transform 160ms var(--ease-out), background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}
.el-button:active:not(.is-disabled) {
  transform: scale(0.97);
}

/* 默认按钮玻璃化 */
.el-button--default:not(.is-plain):not(.is-text):not(.is-link) {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.16);
  color: var(--app-text);
  backdrop-filter: blur(10px);
}
.el-button--default:not(.is-text):not(.is-link):hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
  color: var(--app-text);
}

/* 主按钮：青蓝渐变玻璃 */
.el-button--primary:not(.is-plain):not(.is-text):not(.is-link) {
  background-image: linear-gradient(135deg, #5ad0e6, #6b8bff);
  background-color: #5ad0e6;
  border: none;
  color: #071018;
  font-weight: 600;
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.4) inset, 0 10px 28px -10px rgba(107, 139, 255, 0.6);
}
.el-button--primary:not(.is-plain):not(.is-text):not(.is-link):hover {
  filter: brightness(1.08);
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.5) inset, 0 16px 38px -10px rgba(107, 139, 255, 0.7);
}

/* 表单输入玻璃化（html 前缀提高特异性，防止被按需注入的组件默认样式覆盖） */
html .el-input__wrapper,
html .el-textarea__inner,
html .el-select__wrapper {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.12) inset;
}
html .el-input__wrapper:hover,
html .el-select__wrapper:hover {
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.22) inset;
}
html .el-input__wrapper.is-focus,
html .el-textarea__inner:focus,
html .el-select__wrapper.is-focused {
  box-shadow: 0 0 0 1px rgba(90, 208, 230, 0.6) inset, 0 0 0 4px rgba(90, 208, 230, 0.14) !important;
}
html .el-input__inner,
html .el-textarea__inner {
  color: var(--app-text);
}
html .el-textarea__inner {
  font-family: var(--app-font);
  background: rgba(255, 255, 255, 0.05);
}

/* 下拉菜单 / 弹层玻璃化 */
.el-dropdown-menu,
.el-select__popper.el-popper,
.el-popper {
  background: rgba(20, 27, 46, 0.9) !important;
  backdrop-filter: blur(24px) saturate(150%);
  -webkit-backdrop-filter: blur(24px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
}
.el-popper__arrow::before {
  background: rgba(20, 27, 46, 0.9) !important;
  border-color: rgba(255, 255, 255, 0.14) !important;
}
.el-dropdown-menu__item {
  color: var(--app-text-secondary);
}
.el-dropdown-menu__item:not(.is-disabled):hover {
  background: rgba(90, 208, 230, 0.14);
  color: var(--app-text);
}
.el-select-dropdown__item {
  color: var(--app-text-secondary);
}
.el-select-dropdown__item.is-hovering {
  background: rgba(90, 208, 230, 0.14);
}
.el-select-dropdown__item.is-selected {
  color: var(--app-cyan);
}

/* 对话框玻璃化 */
.el-dialog {
  background: rgba(18, 24, 42, 0.86) !important;
  backdrop-filter: blur(32px) saturate(160%);
  -webkit-backdrop-filter: blur(32px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: var(--app-radius-lg);
  overflow: hidden;
  box-shadow: var(--glass-shadow);
}
.el-dialog__title {
  color: var(--app-text);
  font-weight: 700;
}
.el-dialog__header {
  padding: 20px 24px 8px;
}
.el-dialog__body {
  padding: 12px 24px 8px;
  color: var(--app-text-secondary);
}
.el-dialog__footer {
  padding: 12px 24px 20px;
}
.el-message-box {
  background: rgba(18, 24, 42, 0.9) !important;
  backdrop-filter: blur(28px);
  border: 1px solid rgba(255, 255, 255, 0.16);
}
.el-message-box__title,
.el-message-box__content {
  color: var(--app-text);
}

/* 模态过渡 */
.el-overlay-dialog {
  transition: opacity 0.25s var(--ease-smooth-out);
}
.el-overlay-dialog .el-dialog {
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

/* 消息提示 */
.el-message {
  background: rgba(20, 27, 46, 0.92) !important;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.16) !important;
  border-radius: 12px;
  box-shadow: var(--app-shadow-md);
  transition: transform 0.25s var(--ease-smooth-out), opacity 0.25s var(--ease-smooth-out) !important;
}
.el-message__content {
  color: var(--app-text) !important;
}
.el-message-fade-enter-from,
.el-message-fade-leave-to {
  transform: translateY(8px) scale(0.97);
  opacity: 0;
}

/* 表格深色玻璃 */
html .el-table {
  --el-table-header-bg-color: rgba(255, 255, 255, 0.05);
  --el-table-header-text-color: var(--app-text-secondary);
  --el-table-border-color: rgba(255, 255, 255, 0.08);
  --el-table-row-hover-bg-color: rgba(90, 208, 230, 0.08);
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-text-color: var(--app-text-secondary);
  background: transparent;
  border-radius: 12px;
}
html .el-table th.el-table__cell {
  font-weight: 600;
}
html .el-table,
html .el-table__inner-wrapper::before,
html .el-table--border::after {
  background-color: transparent;
}

/* 分隔线 */
html .el-divider {
  border-color: rgba(255, 255, 255, 0.12);
}
html .el-divider__text {
  font-weight: 600;
  font-size: 13px;
  color: var(--app-text);
  background: var(--app-bg);
}

/* Timeline */
html .el-timeline-item__tail {
  border-left: 2px solid rgba(255, 255, 255, 0.12);
}
.el-timeline-item__node {
  background: var(--app-cyan);
  box-shadow: 0 0 0 4px rgba(90, 208, 230, 0.16);
}
.el-timeline-item__timestamp {
  color: var(--app-text-muted);
}

/* Tabs */
.el-tabs__item {
  color: var(--app-text-secondary);
}
.el-tabs__item.is-active {
  color: var(--app-cyan);
}
.el-tabs__active-bar {
  background-color: var(--app-cyan);
}
.el-tabs__nav-wrap::after {
  background-color: rgba(255, 255, 255, 0.1);
}

/* 标签 Tag 默认玻璃 */
html .el-tag {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.14);
  color: var(--app-text-secondary);
}

/* 进度条轨道 */
html .el-progress-bar__outer {
  background: rgba(255, 255, 255, 0.08);
}

/* 单选/复选 文本 */
.el-radio,
.el-checkbox {
  color: var(--app-text-secondary);
}

/* 单选/复选 框体（深色玻璃化，避免默认全黑/刺眼白）
   关键变量定义在 .el-checkbox / .el-radio 类上，需以更高特异性在同类上覆盖才能生效 */
html .el-checkbox {
  --el-checkbox-bg-color: rgba(90, 208, 230, 0.08);
  --el-checkbox-input-border: 1px solid rgba(90, 208, 230, 0.55);
  --el-checkbox-input-border-color-hover: #5ad0e6;
  --el-checkbox-checked-bg-color: #5ad0e6;
  --el-checkbox-checked-input-border-color: #5ad0e6;
  --el-checkbox-checked-icon-color: #071018;
  --el-checkbox-checked-text-color: #5ad0e6;
  --el-checkbox-disabled-input-fill: rgba(255, 255, 255, 0.05);
  --el-checkbox-disabled-checked-input-fill: rgba(255, 255, 255, 0.2);
  --el-checkbox-disabled-checked-input-border-color: rgba(255, 255, 255, 0.2);
}
html .el-checkbox__inner {
  background-color: rgba(90, 208, 230, 0.08) !important;
  border-color: rgba(90, 208, 230, 0.55) !important;
}
html .el-checkbox__inner:hover {
  background-color: rgba(90, 208, 230, 0.16) !important;
  border-color: #5ad0e6 !important;
}
html .el-checkbox__input.is-checked .el-checkbox__inner,
html .el-checkbox__input.is-indeterminate .el-checkbox__inner,
html .el-checkbox__input.is-checked .el-checkbox__inner:hover,
html .el-checkbox__input.is-indeterminate .el-checkbox__inner:hover {
  background-color: #5ad0e6 !important;
  background-image: linear-gradient(135deg, #5ad0e6, #6b8bff) !important;
  border-color: transparent !important;
}
html .el-checkbox__input.is-checked .el-checkbox__inner:after {
  border-color: #071018 !important;
}
html .el-checkbox__input.is-indeterminate .el-checkbox__inner:before {
  background-color: #071018 !important;
}
html .el-radio {
  --el-radio-input-border-color: rgba(90, 208, 230, 0.55);
  --el-radio-input-border-color-hover: #5ad0e6;
  --el-radio-checked-border-color: #5ad0e6;
  --el-radio-checked-background-color: #5ad0e6;
  --el-radio-checked-icon-color: #071018;
}

/* 描述列表 */
html .el-descriptions {
  --el-descriptions-item-bordered-label-background: rgba(255, 255, 255, 0.05);
  background: transparent;
  color: var(--app-text-secondary);
}
html .el-descriptions__body {
  background: transparent;
  color: var(--app-text-secondary);
}

/* 折叠面板 */
html .el-collapse,
html .el-collapse-item__header,
html .el-collapse-item__wrap {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.1);
  color: var(--app-text);
}

/* 空状态 */
.el-empty__description p {
  color: var(--app-text-muted);
}

/* 骨架屏 */
html .el-skeleton__item {
  background: rgba(255, 255, 255, 0.06);
}

/* ==================== 通用页面元素（玻璃版） ==================== */
.page-banner {
  position: relative;
  overflow: hidden;
  border-radius: var(--app-radius-lg);
  padding: 22px 26px;
  margin-bottom: 20px;
  color: var(--app-text);
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-highlight), var(--app-shadow-sm);
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
  color: var(--app-cyan);
  border: 1px solid rgba(90, 208, 230, 0.3);
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
  background: var(--app-brand-gradient);
}

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
  background: rgba(255, 255, 255, 0.03);
  transition: transform 160ms var(--ease-out), border-color 0.2s ease, background-color 0.2s ease;
}
.history-item:active {
  transform: scale(0.98);
}
@media (hover: hover) and (pointer: fine) {
  .history-item:hover {
    border-color: var(--app-border-strong);
    background: rgba(255, 255, 255, 0.07);
  }
}
.history-item.selected {
  border-color: var(--app-success);
  background: rgba(67, 217, 163, 0.14);
}
.history-item.active {
  border-color: var(--app-cyan);
  background: var(--app-brand-soft);
}

.icon-badge {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #071018;
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

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
</style>