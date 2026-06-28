import api from './client'

export const authAPI = {
  telegram: (initData) => api.post('/auth/telegram', { init_data: initData }),
  demo: (tgId, extra = {}) => api.post('/auth/demo', { tg_id: tgId, ...extra }),
}

export const listingsAPI = {
  list: (params) => api.get('/listings', { params }),
  get: (id) => api.get(`/listings/${id}`),
  my: () => api.get('/listings/my'),
  create: (data) => api.post('/listings', data),
  update: (id, data) => api.put(`/listings/${id}`, data),
  delete: (id) => api.delete(`/listings/${id}`),
}

export const shopsAPI = {
  list: (params) => api.get('/shops', { params }),
  get: (id) => api.get(`/shops/${id}`),
  my: () => api.get('/shops/my'),
  create: (data) => api.post('/shops', data),
  update: (id, data) => api.put(`/shops/${id}`, data),
}

export const searchAPI = {
  search: (params) => api.get('/search', { params }),
}

export const favouritesAPI = {
  list: () => api.get('/favourites'),
  toggleShop: (id) => api.post(`/favourites/shop/${id}`),
  toggleListing: (id) => api.post(`/favourites/listing/${id}`),
}

export const referralAPI = {
  stats: () => api.get('/referral'),
}

export const paymentsAPI = {
  initiate: (data) => api.post('/payments/initiate', data),
  status: (id) => api.get(`/payments/status/${id}`),
  my: () => api.get('/payments/my'),
}

export const notificationsAPI = {
  list: () => api.get('/notifications'),
  readAll: () => api.put('/notifications/read-all'),
  unreadCount: () => api.get('/notifications/unread-count'),
}

export const adminAPI = {
  stats: () => api.get('/admin/stats'),
  users: (params) => api.get('/admin/users', { params }),
  blockUser: (id) => api.post(`/admin/users/${id}/block`),
  unblockUser: (id) => api.post(`/admin/users/${id}/unblock`),
  listings: (params) => api.get('/admin/listings', { params }),
  approveListing: (id) => api.post(`/admin/listings/${id}/approve`),
  rejectListing: (id, reason) => api.post(`/admin/listings/${id}/reject`, { reason }),
  shops: (params) => api.get('/admin/shops', { params }),
  approveShop: (id) => api.post(`/admin/shops/${id}/approve`),
  rejectShop: (id) => api.post(`/admin/shops/${id}/reject`),
  broadcast: (data) => api.post('/admin/broadcast', data),
}

export const messagesAPI = {
  conversations: () => api.get('/conversations'),
  unreadCount: () => api.get('/conversations/unread-count'),
  start: (listingId) => api.post('/conversations', { listing_id: listingId }),
  messages: (convId) => api.get(`/conversations/${convId}/messages`),
  send: (convId, text) => api.post(`/conversations/${convId}/messages`, { text }),
  markRead: (convId) => api.put(`/conversations/${convId}/read`),
}

export const gamificationAPI = {
  myStats: () => api.get('/gamification/my-stats'),
  leaderboard: () => api.get('/gamification/leaderboard'),
}

export const analyticsAPI = {
  my: () => api.get('/analytics/my'),
  admin: () => api.get('/analytics/admin'),
}

export const promotionsAPI = {
  initiate: (data) => api.post('/promotions/initiate', data),
  my: () => api.get('/promotions/my'),
}

export const reviewsAPI = {
  create: (data) => api.post('/reviews', data),
  byUser: (userId) => api.get(`/reviews/user/${userId}`),
  byListing: (listingId) => api.get(`/reviews/listing/${listingId}`),
}

export const uploadAPI = {
  image: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/upload/image', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}
