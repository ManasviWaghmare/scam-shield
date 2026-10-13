import { useEffect, useRef, useState } from 'react'

const API = 'http://127.0.0.1:8001'

const SAMPLES = [
  { label: 'KYC fraud', lang: 'en', text: 'Dear customer your SBI KYC expired urgently verify at http://sbi-kyc-update.xyz within 24 hours else account blocked' },
  { label: 'Lottery (Hindi)', lang: 'hi', text: 'बधाई हो! आपने 25000 की लॉटरी जीती है http://inam-claim.top पर Rs 99 फीस देकर पाएं' },
  { label: 'Job scam (Marathi)', lang: 'mr', text: 'घरबसल्या नोकरी Rs 3000 रोज कमवा आधी Rs 500 UPI वर पाठवा' },
  { label: 'Safe message', lang: 'en', text: 'Meeting at 5pm tomorrow bring the report thanks' },
]

const TICKER = ['Fake KYC expiry', 'UPI refund fraud', 'Part-time job fee scam', 'Lottery prize lure', 'Bank link phishing', 'Digital arrest threat']

const JOB_META = {
  threat_refresh: 'Threat intel · 6h',
  trends: 'Trend digest · hourly',
  purge: 'Privacy purge · daily',
  tip: 'Safety tip · 09:00',
  standup: 'Standup nudge · 21:05',
}

function verdictStyle(v) {
  if (v === 'Scam') return { badge: 'bg-red-600', bar: 'bg-red-500', big: 'text-red-400' }
  if (v === 'Suspicious') return { badge: 'bg-amber-600', bar: 'bg-amber-500', big: 'text-amber-400' }
  return { badge: 'bg-emerald-600', bar: 'bg-emerald-500', big: 'text-emerald-400' }
}

function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem('scamshield-theme') || 'dark')
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    document.documentElement.style.background = theme === 'dark' ? '#04070f' : '#f6f7f6'
    localStorage.setItem('scamshield-theme', theme)
  }, [theme])
  return [theme, setTheme]
}

export default function App() {
  const [theme, setTheme] = useTheme()
  const dark = theme === 'dark'
  const [msg, setMsg] = useState(SAMPLES[0].text)
  const [lang, setLang] = useState('auto')
  const [out, setOut] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [sched, setSched] = useState(null)
  const [trends, setTrends] = useState(null)
  const [alerts, setAlerts] = useState(null)
  const [tab, setTab] = useState('text')
  const fileRef = useRef(null)

  const loadStatus = async () => {
    try {
      const [s, t, a] = await Promise.all([
        fetch(`${API}/scheduler-status`).then(x => x.json()),
        fetch(`${API}/trends`).then(x => x.json()),
        fetch(`${API}/alerts`).then(x => x.json()),
      ])
      setSched(s); setTrends(t); setAlerts(a)
    } catch { /* offline */ }
  }
  useEffect(() => { loadStatus() }, [])

  const check = async () => {
    if (!msg.trim()) { setError('Paste a message first.'); return }
    setLoading(true); setError(''); setOut(null)
    try {
      const r = await fetch(`${API}/check`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, lang: lang === 'auto' ? null : lang }),
      })
      if (!r.ok) throw new Error()
      setOut(await r.json())
      loadStatus()
    } catch { setError('Backend is not running. Start it with: uvicorn main:app --reload') }
    finally { setLoading(false) }
  }

  const checkImage = async (f) => {
    if (!f) return
    setLoading(true); setError(''); setOut(null)
    try {
      const fd = new FormData(); fd.append('file', f)
      const r = await fetch(`${API}/check-image`, { method: 'POST', body: fd })
      const j = await r.json()
      if (j.ocr_text) setMsg(j.ocr_text)
      if (j.error) setError(j.error); else { setOut(j); loadStatus() }
    } catch { setError('Image check failed. Is tesseract installed?') }
    finally { setLoading(false) }
  }

  const speak = () => {
    if (!out?.explanation) return
    const u = new SpeechSynthesisUtterance(out.explanation)
    u.lang = out.lang === 'hi' ? 'hi-IN' : out.lang === 'mr' ? 'mr-IN' : 'en-IN'
    speechSynthesis.speak(u)
  }

  const vs = out ? verdictStyle(out.verdict) : null
  const trendRows = (trends?.trends ?? []).slice().sort((a, b) => b.count - a.count).slice(0, 6)
  const maxCount = Math.max(1, ...trendRows.map(r => r.count))
  const totalScans = trendRows.reduce((n, r) => n + r.count, 0)
  const jobs = sched?.jobs ?? []

  const page = dark
    ? 'min-h-screen bg-[#04070f] text-zinc-100'
    : 'min-h-screen bg-stone-100 text-stone-900'
  const panel = dark ? 'card' : 'bg-white border border-stone-200 rounded-[20px] shadow-sm'
  const sub = dark ? 'text-zinc-400' : 'text-stone-500'
  const input = dark
    ? 'mt-4 w-full border border-white/10 rounded-2xl p-4 text-sm bg-[#070d1d] focus:outline-none focus:ring-2 focus:ring-[#2f6bff]'
    : 'mt-4 w-full border border-stone-200 rounded-2xl p-4 text-sm bg-stone-50 focus:outline-none focus:ring-2 focus:ring-emerald-600'
  const chip = dark
    ? 'text-xs border border-white/10 rounded-full px-3 py-1.5 hover:border-[#2f6bff]'
    : 'text-xs border border-stone-200 rounded-full px-3 py-1.5 hover:border-emerald-600'
  const tabOff = dark ? 'border border-white/10' : 'border border-stone-200'
  const tabOn = dark ? 'bg-zinc-100 text-zinc-900' : 'bg-stone-900 text-white'
  const line = dark ? 'border-white/10' : 'border-stone-200'
  const soft = dark ? 'bg-white/5' : 'bg-stone-100'
  const track = dark ? 'bg-white/10' : 'bg-stone-200'

  return (
    <div className={page}>
      {/* Nav */}
      <header className={`sticky top-0 z-40 backdrop-blur border-b ${dark ? 'bg-[#04070f]/85 border-white/10' : 'bg-white/85 border-stone-200'}`}>
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span className="w-7 h-7 rounded-lg bg-[#2f6bff] text-white flex items-center justify-center font-bold text-sm" style={{ boxShadow: '0 0 18px rgba(47,107,255,.6)' }}>S</span>
            <span className="font-bold tracking-widest text-sm">SCAM SHIELD</span>
          </div>
          <nav className="hidden md:flex items-center gap-7 text-sm opacity-80">
            <a href="#checker" className="hover:opacity-100">Check</a>
            <a href="#live" className="hover:opacity-100">Live intel</a>
            <a href="#how" className="hover:opacity-100">How it works</a>
          </nav>
          <div className="flex items-center gap-2">
            <button onClick={() => setTheme(dark ? 'light' : 'dark')} className={`text-xs border rounded-full px-3.5 py-1.5 ${line}`}>
              {dark ? 'Light' : 'Dark'}
            </button>
            <a href="tel:1930" className={`text-xs border rounded-full px-3.5 py-1.5 ${line}`}>1930 helpline</a>
            <a href="#checker" className="btn-primary text-xs px-4 py-2">Scan message</a>
          </div>
        </div>
      </header>

      {/* Hero — HEXLY style */}
      <section className="relative overflow-hidden">
        {dark && <div className="stars absolute inset-0 pointer-events-none" />}
        <div className="relative max-w-6xl mx-auto px-4 pt-14 pb-2 text-center">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight leading-[1.05]">
            Scam Shield, the AI guardian<br />for your messages
          </h1>
          <p className={`mt-4 text-sm md:text-base ${sub} max-w-xl mx-auto`}>
            Real-time scam detection in English, Hindi and Marathi. Paste any forward, get a verdict with reasons.
          </p>
          <div className="mt-6 flex justify-center gap-3 flex-wrap">
            <button onClick={() => document.getElementById('checker').scrollIntoView({ behavior: 'smooth' })} className="btn-primary px-7 py-2.5 text-sm">Scan my message</button>
            <button onClick={() => document.getElementById('live').scrollIntoView({ behavior: 'smooth' })} className="btn-ghost px-7 py-2.5 text-sm">See live intel</button>
          </div>

          {/* Shield visual */}
          <div className="relative mx-auto mt-10 w-fit">
            <div className="shield-glow absolute -inset-16" />
            <div className="shield mx-auto">
              <div className="shield-inner" />
              <div className="keyhole"><div className="hole-top" /><div className="hole-bottom" /></div>
            </div>
          </div>
        </div>
        {dark && (
          <div className="relative">
            <div className="horizon mx-auto max-w-4xl" />
            <div className="dotgrid h-16 max-w-4xl mx-auto -mt-2" />
          </div>
        )}
      </section>

      {/* Ticker */}
      <div className={`border-y ${line} overflow-hidden`}>
        <div className="max-w-6xl mx-auto px-4 py-2.5 overflow-hidden">
          <div className={`ticker-track text-xs font-semibold tracking-widest ${sub}`}>
            {[...TICKER, ...TICKER].map((t, i) => <span key={i}>● {t.toUpperCase()}</span>)}
          </div>
        </div>
      </div>

      <main className="max-w-6xl mx-auto px-4 pb-16">
        {/* Stats row */}
        <section className="grid grid-cols-3 gap-4 mt-8 max-w-2xl mx-auto text-center">
          {[['87.5%', 'baseline accuracy'], [String(totalScans || '—'), 'scans today'], [`${jobs.length || 5}`, 'auto jobs running']].map(([v, l]) => (
            <div key={l} className={`rounded-2xl border ${line} py-4`}>
              <p className="text-2xl font-bold">{v}</p>
              <p className={`text-xs ${sub}`}>{l}</p>
            </div>
          ))}
        </section>

        {/* Checker */}
        <section id="checker" className={`mt-8 ${panel} overflow-hidden`}>
          <div className="grid lg:grid-cols-2">
            <div className={`p-6 border-b lg:border-b-0 lg:border-r ${line}`}>
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex gap-2 text-sm">
                  <button onClick={() => setTab('text')} className={`px-4 py-1.5 rounded-full ${tab === 'text' ? tabOn : tabOff}`}>Text</button>
                  <button onClick={() => setTab('image')} className={`px-4 py-1.5 rounded-full ${tab === 'image' ? tabOn : tabOff}`}>Screenshot</button>
                </div>
                <select value={lang} onChange={e => setLang(e.target.value)} className="text-sm border rounded-full px-3 py-1.5 bg-transparent" style={{ borderColor: 'inherit' }}>
                  <option value="auto">Auto</option><option value="en">English</option>
                  <option value="hi">Hindi</option><option value="mr">Marathi</option>
                </select>
              </div>
              {tab === 'text' ? (
                <textarea value={msg} onChange={e => setMsg(e.target.value)} rows={7}
                  placeholder="Paste the SMS or WhatsApp forward here…"
                  className={input} />
              ) : (
                <div className={`mt-4 border border-dashed rounded-2xl p-8 text-center ${line}`}>
                  <p className={`text-sm ${sub}`}>WhatsApp screenshot → OCR → same verdict.</p>
                  <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={e => checkImage(e.target.files[0])} />
                  <button onClick={() => fileRef.current?.click()} className="btn-ghost px-5 py-2 mt-3 text-sm">Choose image</button>
                </div>
              )}
              <div className="mt-3 flex flex-wrap gap-2">
                {SAMPLES.map(s => (
                  <button key={s.label} onClick={() => { setMsg(s.text); setLang(s.lang); setTab('text') }} className={chip}>{s.label}</button>
                ))}
              </div>
              <button onClick={check} disabled={loading} className="btn-primary w-full py-3 mt-4">{loading ? 'Analysing…' : 'Analyse now'}</button>
              {error && <p className="mt-3 text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-2xl p-3">{error}</p>}
            </div>

            <div className="p-6">
              {loading && (
                <div className="space-y-3">
                  <div className="skeleton h-10 w-48 rounded-full" />
                  <div className="skeleton h-24 w-full rounded-2xl" />
                  <div className="skeleton h-4 w-full rounded" />
                </div>
              )}
              {!loading && !out && (
                <div className="h-full flex flex-col justify-center text-center py-10">
                  <p className={`text-5xl font-bold ${dark ? 'text-white/10' : 'text-stone-200'}`}>?</p>
                  <p className="mt-3 font-semibold">Verdict lands here</p>
                  <p className={`mt-1 text-sm ${sub}`}>Score, triggers, links and what to do next.</p>
                </div>
              )}
              {!loading && out && !out.error && (
                <div className="rise">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className={`text-white text-sm font-bold px-4 py-1.5 rounded-full ${vs.badge}`}>{out.verdict}</span>
                    <span className={`text-3xl font-bold ${vs.big}`}>{(out.score * 100).toFixed(0)}%</span>
                    <span className={`text-xs ml-auto ${sub}`}>{out.category} · {out.lang?.toUpperCase()}</span>
                  </div>
                  <div className={`mt-3 h-2 rounded-full overflow-hidden ${track}`}>
                    <div className={`h-full ${vs.bar}`} style={{ width: `${Math.round(out.score * 100)}%`, boxShadow: '0 0 12px currentColor' }} />
                  </div>
                  <p className="mt-4 text-sm leading-relaxed">{out.explanation}</p>
                  <ul className="mt-3 space-y-1.5">
                    {(out.signals || []).slice(0, 3).map((s, i) => (
                      <li key={i} className="text-sm border-l-2 border-[#2f6bff] pl-3 opacity-90">{s}</li>
                    ))}
                  </ul>
                  <p className={`mt-3 text-xs ${sub}`}>Links: {(out.urls || []).join(', ') || 'none'} · Triggers: {(out.highlights || []).join(', ') || 'none'}</p>
                  {(out.model_tokens || []).length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {(out.model_tokens || []).slice(0, 6).map((t, i) => (
                        <span key={i} title={`weight ${t.weight}`} className={`text-xs px-2 py-0.5 rounded-full border ${line}`}>{t.token}</span>
                      ))}
                      <span className={`text-xs ${sub}`}>model evidence</span>
                    </div>
                  )}
                  <div className="mt-4 flex gap-2 flex-wrap">
                    <button onClick={speak} className="btn-ghost text-sm px-4 py-2">Listen</button>
                    <a href="tel:1930" className="btn-primary text-sm px-4 py-2">Call 1930</a>
                    <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer" className="btn-ghost text-sm px-4 py-2">Report</a>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Live intel */}
        <section id="live" className="mt-8 grid lg:grid-cols-3 gap-6">
          <div className={`lg:col-span-2 ${panel} p-6`}>
            <div className="flex items-baseline justify-between">
              <h2 className="text-xl font-bold">What scammers are trying today</h2>
              <span className={`text-xs ${sub}`}>hourly · anonymised</span>
            </div>
            <div className="mt-5 space-y-4">
              {trendRows.length === 0 && <p className={`text-sm ${sub}`}>Run a few checks to fill this.</p>}
              {trendRows.map((r, i) => (
                <div key={i} className="grid grid-cols-12 items-center gap-3">
                  <span className="col-span-4 text-sm font-medium truncate">{r.category}</span>
                  <div className={`col-span-6 h-2.5 rounded-full overflow-hidden ${track}`}>
                    <div className="h-full bg-[#2f6bff] rounded-full" style={{ width: `${Math.round((r.count / maxCount) * 100)}%`, boxShadow: '0 0 10px rgba(47,107,255,.7)' }} />
                  </div>
                  <span className="col-span-2 text-right font-mono font-bold text-sm">{r.count}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="space-y-6">
            <div className={`${panel} p-5`}>
              <h3 className="font-bold text-sm tracking-widest">NEXT AUTO RUNS</h3>
              <div className="mt-2 space-y-2">
                {jobs.slice(0, 4).map(j => (
                  <div key={j.id} className="flex justify-between text-sm">
                    <span className="opacity-80">{JOB_META[j.id] ?? j.id}</span>
                    <span className="font-mono text-xs">{j.next ? new Date(j.next).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '—'}</span>
                  </div>
                ))}
                {jobs.length === 0 && <p className={`text-sm ${sub}`}>Backend offline.</p>}
              </div>
            </div>
            <div className={`${panel} p-5`}>
              <h3 className="font-bold text-sm tracking-widest">SAFETY NOTES</h3>
              <ul className="mt-2 space-y-2 text-sm opacity-80 max-h-36 overflow-auto">
                {(alerts?.alerts ?? []).slice(-3).reverse().map((a, i) => <li key={i} className="border-l-2 border-[#2f6bff] pl-2">{String(a).slice(0, 100)}</li>)}
                {(!alerts?.alerts?.length) && <li>First note appears after a check.</li>}
              </ul>
            </div>
          </div>
        </section>

        {/* Steps + emergency */}
        <section id="how" className={`mt-8 ${panel} p-6`}>
          <div className="grid sm:grid-cols-4 gap-5">
            {[['Paste', 'Message or screenshot, any language'], ['Score', 'Model plus rules, one risk number'], ['Explain', 'Triggers in plain words'], ['Act', 'Block, call 1930, warn others']].map(([h, b], i) => (
              <div key={h} className="flex gap-3">
                <span className={`text-3xl font-bold ${dark ? 'text-white/15' : 'text-stone-200'}`}>{i + 1}</span>
                <div><p className="font-bold text-sm">{h}</p><p className={`text-xs mt-1 ${sub}`}>{b}</p></div>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-8 rounded-[20px] bg-[#2f6bff] text-white p-6 md:p-8 flex flex-wrap items-center gap-4 justify-between" style={{ boxShadow: '0 0 50px rgba(47,107,255,.35)' }}>
          <div>
            <p className="text-xl font-bold">Already clicked or paid?</p>
            <p className="text-sm text-blue-100 mt-1">Call 1930 immediately, then file at cybercrime.gov.in.</p>
          </div>
          <div className="flex gap-3">
            <a href="tel:1930" className="bg-white text-blue-900 font-bold text-sm px-6 py-3 rounded-full">Call 1930 now</a>
            <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer" className="border border-blue-200 text-sm px-6 py-3 rounded-full">File report</a>
          </div>
        </section>

        <footer className={`mt-8 border-t ${line} pt-5 text-xs ${sub} flex flex-wrap gap-2 justify-between`}>
          <span>SCAM SHIELD · Hack-A-Throne 2026 · AI Guardian for your messages</span>
          <span>Hashes only · raw messages deleted in 24 hours</span>
        </footer>
      </main>
    </div>
  )
}
