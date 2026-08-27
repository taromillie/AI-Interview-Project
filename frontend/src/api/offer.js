import request from './http'

export function createOffer(payload) {
  return request.post('/offers', payload)
}

export function listOffers() {
  return request.get('/offers')
}

export function updateOffer(id, payload) {
  return request.put(`/offers/${id}`, payload)
}

export function deleteOffer(id) {
  return request.delete(`/offers/${id}`)
}

export function compareOffers() {
  return request.post('/offers/compare')
}
