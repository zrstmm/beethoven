const API_BASE = '/api'

function getToken() {
  return localStorage.getItem('beethoven_token')
}

export function setToken(token) {
  localStorage.setItem('beethoven_token', token)
}

export function clearToken() {
  localStorage.removeItem('beethoven_token')
}

export function isAuthenticated() {
  return !!getToken()
}

async function request(path, options = {}) {
  const headers = { ...options.headers }
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(options.body)
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (res.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json()
}

export async function login(password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: { password },
  })
  setToken(data.token)
  return data
}

export async function getClients(city, weekStart) {
  return request(`/clients?city=${city}&week_start=${weekStart}`)
}

export async function getClientDetail(id) {
  return request(`/clients/${id}`)
}

export async function getAnalytics(city, dateFrom, dateTo) {
  return request(`/analytics?city=${city}&date_from=${dateFrom}&date_to=${dateTo}`)
}

export async function getSettings() {
  return request('/settings')
}

export async function updateSetting(key, value) {
  return request(`/settings/${key}`, {
    method: 'PUT',
    body: { value },
  })
}
