import http from './http'

// 转行诊断
export function careerDiagnosis(data) {
  return http.post('/career/diagnosis', data)
}

// 转行诊断历史
export function listCareerPlans() {
  return http.get('/career/plans')
}
