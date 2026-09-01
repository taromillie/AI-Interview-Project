import { nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'

/**
 * 视频模式摄像头管理：开启 / 关闭 / 画面活动监测。
 *
 * 依赖注入（父组件提供）：
 * - getMicSupported(): boolean —— 浏览器是否支持语音识别，决定降级目标
 * - setAnswerMode(mode) —— 摄像头不可用时回退到 voice/text
 *
 * 视频模式降级：摄像头失败 → 语音（语音不可用 → 文字），不阻塞面试主流程。
 */
export function useCamera({ getMicSupported, setAnswerMode }) {
  const camEnabled = ref(false) // 视频轨道是否已开启
  const camError = ref('') // 摄像头失败原因
  const camActive = ref(true) // 画面活动检测结果（默认视为正常）
  const videoRef = ref(null)
  let camStream = null
  let camTracks = []
  let activityTimer = null
  let lastFrame = null

  // 每 4s 截一帧到小 canvas，与上一帧比较像素差 → 画面是否有人活动（轻量方案，无需 face-api）
  function startActivityCheck() {
    if (activityTimer) return
    lastFrame = null
    camActive.value = true
    activityTimer = setInterval(() => {
      const v = videoRef.value
      if (!v || v.readyState < 2) return
      const canvas = document.createElement('canvas')
      canvas.width = 96
      canvas.height = 72
      const ctx = canvas.getContext('2d')
      if (!ctx) return
      ctx.drawImage(v, 0, 0, 96, 72)
      let data
      try {
        data = ctx.getImageData(0, 0, 96, 72).data
      } catch {
        return
      }
      if (lastFrame) {
        let diff = 0
        for (let i = 0; i < data.length; i += 32) {
          diff += Math.abs(data[i] - lastFrame[i])
        }
        camActive.value = diff > 700
      }
      lastFrame = data
    }, 4000)
  }

  function stopCamera() {
    if (activityTimer) {
      clearInterval(activityTimer)
      activityTimer = null
    }
    lastFrame = null
    camActive.value = true
    camTracks.forEach((t) => {
      try {
        t.stop()
      } catch {
        /* 忽略 */
      }
    })
    camTracks = []
    if (videoRef.value) videoRef.value.srcObject = null
    camStream = null
    camEnabled.value = false
  }

  function fallbackVideoMode() {
    stopCamera()
    const next = getMicSupported() ? 'voice' : 'text'
    setAnswerMode(next)
    ElMessage.warning(`${camError.value}，已切换为${next === 'voice' ? '语音' : '文字'}回答`)
  }

  async function enableCamera() {
    if (camStream) return
    if (!navigator.mediaDevices?.getUserMedia) {
      camError.value = '当前浏览器不支持摄像头'
      fallbackVideoMode()
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: false,
      })
      camStream = stream
      camTracks = stream.getVideoTracks()
      camEnabled.value = true
      camError.value = ''
      await nextTick()
      if (videoRef.value) {
        videoRef.value.srcObject = stream
        videoRef.value.play().catch(() => {})
      }
      startActivityCheck()
    } catch {
      camError.value = '摄像头不可用或未授权'
      fallbackVideoMode()
    }
  }

  function toggleCamera() {
    if (camStream) stopCamera()
    else enableCamera()
  }

  return {
    camEnabled,
    camError,
    camActive,
    videoRef,
    startActivityCheck,
    stopCamera,
    enableCamera,
    toggleCamera,
  }
}
