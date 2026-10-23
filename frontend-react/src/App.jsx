import { useEffect, useState } from 'react'
import { loadAll } from './lib/api.js'
import { cls } from './lib/ui.js'
import Layout from './components/Layout.jsx'
import Home from './pages/Home.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Learn from './pages/Learn.jsx'
import Chat from './pages/Chat.jsx'
import About from './pages/About.jsx'

function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem('scamshield-theme') || 'dark')
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    document.documentElement.style.background = theme === 'dark' ? '#04070f' : '#f6f7f6'
    localStorage.setItem('scamshield-theme', theme)
  }, [theme])
  return [theme, setTheme]
}

function useRoute() {
  const get = () => window.location.hash.replace(/^#/, '') || '/'
  const [route, setRoute] = useState(get())
  useEffect(() => {
    const fn = () => { setRoute(get()); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', fn)
    return () => window.removeEventListener('hashchange', fn)
  }, [])
  return route
}

const EMPTY = { sched: null, trends: null, alerts: null, history: null, stats: null }

export default function App() {
  const [theme, setTheme] = useTheme()
  const route = useRoute()
  const [data, setData] = useState(EMPTY)

  const refresh = async () => {
    try { setData(await loadAll()) } catch { /* backend offline */ }
  }
  useEffect(() => { refresh() }, [])

  const c = cls(theme === 'dark')

  return (
    <Layout c={c} route={'#' + route} theme={theme} setTheme={setTheme}>
      {route === '/' && <Home c={c} data={data} refresh={refresh} />}
      {route === '/dashboard' && <Dashboard c={c} data={data} refresh={refresh} />}
      {route === '/learn' && <Learn c={c} />}
      {route === '/chat' && <Chat c={c} />}
      {route === '/about' && <About c={c} />}
      {!['/', '/dashboard', '/learn', '/chat', '/about'].includes(route) && <Home c={c} data={data} refresh={refresh} />}
    </Layout>
  )
}
