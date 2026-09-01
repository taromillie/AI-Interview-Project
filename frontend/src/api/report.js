import http from './http'

export function getReport(reportId) {
  return http.get(`/reports/${reportId}`)
}

export function getReportStatus(interviewId) {
  return http.get(`/reports/interviews/${interviewId}/status`)
}

export function regenerateReport(reportId) {
  return http.post(`/reports/${reportId}/regenerate`)
}
