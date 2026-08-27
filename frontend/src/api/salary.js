import http from './http'

// 谈薪评估
export function salaryEvaluate(data) {
  return http.post('/salary/evaluate', data)
}

// 谈薪评估历史
export function listSalaryEvals() {
  return http.get('/salary/evals')
}
