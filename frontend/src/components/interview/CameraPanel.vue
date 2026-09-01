<template>
  <aside class="cam-panel">
    <div class="cam-title"><span class="cam-dot"></span>我的画面</div>
    <video v-show="camEnabled" :ref="setVideoRef" autoplay muted playsinline></video>
    <div v-if="!camEnabled" class="cam-empty">
      <el-icon :size="18"><VideoCamera /></el-icon>
      <span>{{ camError || '摄像头未开启' }}</span>
    </div>
    <div v-else class="cam-status" :class="{ idle: !camActive }">
      {{ camActive ? '画面正常' : '画面静止，请靠近摄像头' }}
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { VideoCamera } from '@element-plus/icons-vue'

const props = defineProps({
  camEnabled: { type: Boolean, default: false },
  camError: { type: String, default: '' },
  camActive: { type: Boolean, default: true },
})
const emit = defineEmits(['video-el'])

const videoEl = ref(null)
// 视频元素挂载/卸载时上报父组件，供 useCamera 的 videoRef 绑定流
function setVideoRef(el) {
  videoEl.value = el
  emit('video-el', el)
}
</script>

<style scoped>
.cam-panel {
  width: 200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cam-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--app-text);
}
.cam-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.18);
}
.cam-panel video {
  width: 100%;
  border-radius: 12px;
  background: #0d1117;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  border: 1px solid rgba(226, 232, 240, 0.6);
}
.cam-empty {
  aspect-ratio: 4 / 3;
  border-radius: 12px;
  background: #111827;
  border: 1px dashed #3a4356;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #8b95a7;
  font-size: 12px;
}
.cam-status {
  font-size: 12px;
  color: #10b981;
  text-align: center;
}
.cam-status.idle {
  color: #f59e0b;
}

@media (max-width: 900px) {
  .cam-panel {
    width: 100%;
    flex-direction: row;
    align-items: center;
    gap: 12px;
  }
  .cam-panel video,
  .cam-empty {
    width: 140px;
    aspect-ratio: 4 / 3;
  }
  .cam-title {
    min-width: 90px;
  }
}
</style>
