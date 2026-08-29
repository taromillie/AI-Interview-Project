import http from './http'

// 根据简历智能匹配岗位（覆盖保存为该简历的最新推荐结果）
export function matchPositions(resumeId, params) {
  return http.post(`/resumes/${resumeId}/match-positions`, params || {})
}

// 该简历最近一次的匹配推荐记录（含岗位快照）
export function listResumeMatches(resumeId) {
  return http.get(`/resumes/${resumeId}/matches`)
}

// 清空该简历的匹配推荐记录
export function clearResumeMatches(resumeId) {
  return http.delete(`/resumes/${resumeId}/matches`)
}
