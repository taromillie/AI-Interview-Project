import http from './http'

export function listPositions() {
  return http.get('/questions/positions')
}

// 岗位方向聚合（岗位广场方向卡）：方向名 + 公司数 + 技能 + 平均薪资 + 方向岗位列表
export function listDirections() {
  return http.get('/questions/positions/directions')
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

// AI 一键生成题目（预览，不入库）
export function generateAtoms({ topic, position_id = null, count = 3 }) {
  return http.post('/questions/generate', { topic, position_id, count })
}

// 批量保存 AI 生成的题目（草稿）
export function saveGeneratedAtoms({ position_id, items }) {
  return http.post('/questions/generate/save', { position_id, items })
}
