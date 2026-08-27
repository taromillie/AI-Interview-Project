import http from './http'

export function listPositions() {
  return http.get('/questions/positions')
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
