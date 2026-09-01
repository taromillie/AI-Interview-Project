import { ref } from 'vue'
import { ElMessage } from 'element-plus'

/**
 * 语音面试能力：语音播报（speechSynthesis）+ 语音识别输入（Web Speech API）。
 *
 * 依赖注入（父组件提供）：
 * - getWaitingAnswer(): boolean —— 是否等待用户回答（录音只能在等待期进行）
 * - getAnswerMode(): string —— 当前回答方式（text/voice/video）
 * - getIsUnmounted(): boolean —— 组件是否已卸载（卸载后禁止自动开麦）
 * - setAnswerDraft(text) —— 识别结果写回回答输入框
 */
export function useVoice({ getWaitingAnswer, getAnswerMode, getIsUnmounted, setAnswerDraft }) {
  const voiceEnabled = ref(true)
  const micSupported =
    typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)
  const recording = ref(false)
  let finalTranscript = ''
  let recognition = null

  // ── 语音播报 ──
  function speakText(text) {
    if (!voiceEnabled.value || !text) return
    if (!('speechSynthesis' in window)) return
    stopSpeak()
    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'zh-CN'
    u.rate = 1.05
    // 播报自然结束（未被提前停止）时也自动开麦
    u.onend = () => {
      maybeAutoStartMic()
    }
    u.onerror = () => {
      maybeAutoStartMic()
    }
    window.speechSynthesis.speak(u)
  }

  function stopSpeak() {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel()
  }

  function toggleVoice() {
    voiceEnabled.value = !voiceEnabled.value
    if (!voiceEnabled.value) stopSpeak()
  }

  // ── 语音输入 ──
  function getRecognition() {
    if (recognition) return recognition
    const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!Ctor) return null
    const r = new Ctor()
    r.lang = 'zh-CN'
    r.continuous = true
    r.interimResults = true
    r.onresult = (e) => {
      // 识别已停止（如用户已按 Enter 发送）后不再覆盖输入框，避免 stop() 的收尾结果清空内容
      if (!recording.value) return
      let interim = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i]
        if (res.isFinal) finalTranscript += res[0].transcript
        else interim += res[0].transcript
      }
      setAnswerDraft((finalTranscript + interim).trimStart())
    }
    r.onerror = (e) => {
      // 自动开麦后用户可能尚未开口：no-speech 属正常，保持录音并重启识别
      if (e?.error === 'no-speech' && recording.value && getWaitingAnswer()) {
        try {
          r.start()
        } catch {
          recording.value = false
        }
        return
      }
      recording.value = false
    }
    r.onend = () => {
      if (recording.value) {
        try {
          r.start()
        } catch {
          recording.value = false
        }
      }
    }
    recognition = r
    return r
  }

  function stopRecording() {
    if (!recording.value) return
    recording.value = false
    if (recognition) {
      try {
        recognition.stop()
      } catch {
        /* 忽略 */
      }
    }
  }

  function startRecording() {
    if (!micSupported) return false
    const r = getRecognition()
    if (!r) return false
    if (recording.value) return true
    finalTranscript = ''
    setAnswerDraft('')
    recording.value = true
    try {
      r.start()
      return true
    } catch {
      recording.value = false
      return false
    }
  }

  function toggleRecording() {
    if (!micSupported || !getWaitingAnswer()) return
    if (recording.value) {
      stopRecording()
      return
    }
    if (!startRecording()) {
      ElMessage.warning('无法启动麦克风，请检查浏览器权限')
    }
  }

  // AI 回答后自动开麦（语音/视频模式）：问题已完整显示在屏幕上，直接开麦让用户开口回答。
  // 若 AI 语音播报还在进行，先停止播报，避免其声音被识别进用户回答；
  // 不再等待播报结束（之前按播报时长等待导致麦克风迟迟不打开）。
  function maybeAutoStartMic() {
    if (getIsUnmounted()) return
    if (!micSupported || !getWaitingAnswer()) return
    if (getAnswerMode() === 'text') return
    if (recording.value) return
    if ('speechSynthesis' in window && (window.speechSynthesis.speaking || window.speechSynthesis.pending)) {
      stopSpeak()
    }
    startRecording()
  }

  // 组件卸载时统一清理：停止播报、停止识别并释放 recognition 实例
  function dispose() {
    stopSpeak()
    stopRecording()
    if (recognition) {
      try {
        recognition.abort()
      } catch {
        /* 忽略 */
      }
      recognition = null
    }
  }

  return {
    voiceEnabled,
    micSupported,
    recording,
    speakText,
    stopSpeak,
    toggleVoice,
    startRecording,
    stopRecording,
    toggleRecording,
    maybeAutoStartMic,
    dispose,
  }
}
