import api from './client'

export const authAPI = {
  telegram: (initData) => api.post('/auth/telegram', { init_data: initData }),
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
}

export const notificationsAPI = {
  list: () => api.get('/notifications'),
  readAll: () => api.put('/notifications/read-all'),
  unreadCount: () => api.get('/notifications/unread-count'),
}

export const uploadAPI = {
  image: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/upload/image', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}
