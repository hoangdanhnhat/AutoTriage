import client from './client'

export const listInventories = () =>
  client.get('/inventories').then((r) => r.data)

export const getInventory = (id) =>
  client.get(`/inventories/${id}`).then((r) => r.data)

export const getInventoryNodes = (id) =>
  client.get(`/inventories/${id}/nodes`).then((r) => r.data)

export const checkInventoryStatus = (id) =>
  client.post(`/inventories/${id}/check-status`).then((r) => r.data)

export const uploadInventory = (name, file) => {
  const fd = new FormData()
  fd.append('name', name)
  fd.append('file', file)
  return client.post('/inventories', fd).then((r) => r.data)
}

export const deleteInventory = (id) =>
  client.delete(`/inventories/${id}`)
