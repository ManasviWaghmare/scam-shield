const CACHE = 'scamshield-v1'
const SHELL = ['/', '/index.html', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png']

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => c.addAll(SHELL).catch(() => {}))
      .then(() => self.skipWaiting())
  )
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  )
})

const isApi = (url) =>
  url.port === '8001' ||
  ['/trends', '/stats', '/scheduler-status', '/alerts', '/history', '/report-info'].includes(url.pathname) ||
  url.pathname.startsWith('/assistant')

self.addEventListener('fetch', (e) => {
  const req = e.request
  if (req.method !== 'GET') return
  const url = new URL(req.url)

  // Hashed production assets: cache-first, refreshed in background
  if (url.origin === self.location.origin && url.pathname.startsWith('/assets/')) {
    e.respondWith(
      caches.match(req).then((hit) => {
        const fresh = fetch(req)
          .then((res) => {
            if (res.ok) caches.open(CACHE).then((c) => c.put(req, res.clone()))
            return res
          })
          .catch(() => hit)
        return hit || fresh
      })
    )
    return
  }

  // API GETs (read-only): network-first, cached copy when offline
  if (isApi(url)) {
    e.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) caches.open(CACHE).then((c) => c.put(req, res.clone()))
          return res
        })
        .catch(() =>
          caches.match(req).then(
            (r) => r || new Response(JSON.stringify({ error: 'offline', detail: 'network unavailable' }), {
              status: 503,
              headers: { 'Content-Type': 'application/json' },
            })
          )
        )
    )
    return
  }

  // Pages & dev modules: network-first so edits always show, cache fallback offline
  e.respondWith(
    fetch(req)
      .then((res) => {
        if (res.ok) caches.open(CACHE).then((c) => c.put(req, res.clone()))
        return res
      })
      .catch(() => caches.match(req).then((r) => r || caches.match('/index.html')))
  )
})
