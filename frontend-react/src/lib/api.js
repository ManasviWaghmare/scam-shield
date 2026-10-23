export const API = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001').replace(/\/$/, '')

export async function checkMessage(message, lang = null) {
  const r = await fetch(`${API}/check`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, lang }),
  })
  if (!r.ok) throw new Error('backend error')
  return r.json()
}

export async function assistantHealth() {
  const r = await fetch(`${API}/assistant/health`)
  if (!r.ok) throw new Error('assistant unavailable')
  return r.json()
}

export async function assistantChat(question, message = '', lang = 'en', history = []) {
  const r = await fetch(`${API}/assistant/chat`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, message, lang, history }),
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error(err.detail || `assistant error ${r.status}`)
  }
  return r.json()
}

export async function assistantSources() {
  const r = await fetch(`${API}/assistant/sources`)
  if (!r.ok) throw new Error('sources unavailable')
  return r.json()
}

export async function checkImage(file) {
  const fd = new FormData()
  fd.append('file', file)
  const r = await fetch(`${API}/check-image`, { method: 'POST', body: fd })
  if (!r.ok) throw new Error('ocr error')
  return r.json()
}

export async function loadAll() {
  const [sched, trends, alerts, history, stats] = await Promise.all([
    fetch(`${API}/scheduler-status`).then(x => x.json()),
    fetch(`${API}/trends`).then(x => x.json()),
    fetch(`${API}/alerts`).then(x => x.json()),
    fetch(`${API}/history?limit=8`).then(x => x.json()),
    fetch(`${API}/stats`).then(x => x.json()),
  ])
  return { sched, trends, alerts, history, stats }
}

export async function speakServerSide(text, lang) {
  const r = await fetch(`${API}/speak`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, lang }),
  })
  if (r.ok && (r.headers.get('content-type') || '').includes('audio')) {
    new Audio(URL.createObjectURL(await r.blob())).play()
    return true
  }
  return false
}

export function speakBrowser(text, lang) {
  const u = new SpeechSynthesisUtterance(text)
  u.lang = lang === 'hi' ? 'hi-IN' : lang === 'mr' ? 'mr-IN' : 'en-IN'
  speechSynthesis.speak(u)
}

async function jsonOrThrow(r, fallback) {
  if (r.ok) return r.json()
  const err = await r.json().catch(() => ({}))
  throw new Error(err.detail || fallback || `request failed ${r.status}`)
}

export async function subscribeAlerts(phone, name, consent) {
  return jsonOrThrow(await fetch(`${API}/alerts/subscribe`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, name, consent }),
  }), 'Subscription failed')
}

export async function pendingAlerts(adminKey) {
  return jsonOrThrow(await fetch(`${API}/alerts/pending`, {
    headers: adminKey ? { 'X-Admin-Key': adminKey } : {},
  }), 'Could not load review queue')
}

export async function approveAlert(item, adminKey) {
  return jsonOrThrow(await fetch(`${API}/alerts/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(adminKey ? { 'X-Admin-Key': adminKey } : {}) },
    body: JSON.stringify({ url: item.url, how_it_works: item.how_it_works, action: item.action }),
  }), 'Approval failed')
}

export async function sendApprovedAlerts(adminKey) {
  return jsonOrThrow(await fetch(`${API}/alerts/send`, {
    method: 'POST', headers: adminKey ? { 'X-Admin-Key': adminKey } : {},
  }), 'Send failed')
}
