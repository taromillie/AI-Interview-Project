import request from './http'

export function generateStudyPlan(payload) {
  return request.post('/study-plan/generate', payload)
}

export function listStudyPlans() {
  return request.get('/study-plan/plans')
}

export function toggleStudyPlanTask(planId, day, done) {
  return request.patch(`/study-plan/${planId}`, { day, done })
}

export function deleteStudyPlan(planId) {
  return request.delete(`/study-plan/${planId}`)
}
