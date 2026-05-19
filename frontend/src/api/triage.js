import client from './client'

export const listJobs = () =>
  client.get('/triage/jobs').then((r) => r.data)

export const getJob = (id) =>
  client.get(`/triage/jobs/${id}`).then((r) => r.data)

export const createJob = (payload) =>
  client.post('/triage/jobs', payload).then((r) => r.data)

export const startJob = (id) =>
  client.post(`/triage/jobs/${id}/start`).then((r) => r.data)

export const listArtifacts = (id) =>
  client.get(`/triage/jobs/${id}/artifacts`).then((r) => r.data)

export const downloadArtifact = (id, path) =>
  client.get(`/triage/jobs/${id}/artifacts/download`, {
    params: { path },
    responseType: 'blob',
  })
