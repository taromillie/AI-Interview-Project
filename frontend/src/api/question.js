import http from './http'

export function listPositions() {
  return http.get('/questions/positions')
}

export function syncPositions() {
  return http.post('/questions/positions/sync')
}

export function getSyncConfig() {
  return http.get('/questions/positions/sync-config')
}

export function updateSyncConfig(params = {}) {
  return http.post('/questions/positions/sync-config', null, { params })
}

export function listAtoms(params = {}) {
  return http.get('/questions', { params })
}

export function createAtom({ position_id, question, reference_points = [], tags = [], difficulty = 'mid' }) {
  return http.post('/questions', null, {
    params: {
      position_id,
      question,
      reference_points,
      tags,
      difficulty,
    },
  })
}

export function publishAtom(atomId) {
  return http.post(`/questions/${atomId}/publish`)
}

export function importAtoms({ position_id, format = 'auto', text }) {
  return http.post('/questions/import', { position_id, format, text })
}
