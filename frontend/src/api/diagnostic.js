import http from './http'

// 上传简历（粘贴文本），name 可选：留空自动命名
export function uploadResumeText(rawText, name) {
  const form = new FormData()
  form.append('raw_text', rawText)
  if (name) form.append('name', name)
  return http.post('/resumes/upload', form)
}

// 上传简历（PDF/TXT 文件），name 可选：留空自动命名
export function uploadResumeFile(file, name) {
  const form = new FormData()
  form.append('file', file)
  if (name) form.append('name', name)
  return http.post('/resumes/upload', form)
}

// 我的简历列表
export function listResumes() {
  return http.get('/resumes')
}

// 更新历史简历（粘贴文本），name 可选：留空则保留原名
export function updateResume(id, rawText, name) {
  const form = new FormData()
  form.append('raw_text', rawText)
  if (name) form.append('name', name)
  return http.put(`/resumes/${id}`, form)
}

// 更新历史简历（重新上传文件），name 可选：留空则保留原名
export function updateResumeFile(id, file, name) {
  const form = new FormData()
  form.append('file', file)
  if (name) form.append('name', name)
  return http.put(`/resumes/${id}`, form)
}

// 删除历史简历（连带删除其匹配诊断记录）
export function deleteResume(id) {
  return http.delete(`/resumes/${id}`)
}

// 简历×JD 匹配诊断（可指定简历与历史 JD）
export function diagnose({ jd_text, resume_id, jd_id }) {
  return http.post('/resumes/diagnose', {
    jd_text: jd_text || undefined,
    resume_id: resume_id || undefined,
    jd_id: jd_id || undefined,
  })
}

// JD 历史列表
export function listJds() {
  return http.get('/jds')
}

// 保存 JD
export function createJd({ title, content }) {
  return http.post('/jds', { title, content })
}

// 更新 JD
export function updateJd(id, { title, content }) {
  return http.put(`/jds/${id}`, { title, content })
}

// 删除 JD
export function deleteJd(id) {
  return http.delete(`/jds/${id}`)
}
