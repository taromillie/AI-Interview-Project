import http from './http'

export function getReport(reportId) {
  return http.get(`/reports/${reportId}`)
}
