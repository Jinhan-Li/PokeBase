// frontend/src/api/index.js
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 90000
})

export function chat(question) {
  return api.post('/chat', { question })
}

export function query(cypher) {
  return api.post('/query', { cypher })
}

export function getSchema() {
  return api.get('/schema')
}

export function health() {
  return api.get('/health')
}
