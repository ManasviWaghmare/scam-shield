import { useRef, useState } from 'react'
import { checkMessage, checkImage, speakServerSide, speakBrowser } from '../lib/api.js'

const SAMPLES = [
  { label: 'KYC fraud', lang: 'en', text: 'Dear customer your SBI KYC expired urgently verify at http://sbi-kyc-update.xyz within 24 hours else account blocked' },
  { label: 'Lottery (Hindi)', lang: 'hi', text: 'बधाई हो! आपने 25000 की लॉटरी जीती है http://inam-claim.top पर Rs 99 फीस देकर पाएं' },
  { label: 'Job scam (Marathi)', lang: 'mr', text: 'घरबसल्या नोकरी Rs 3000 रोज कमवा आधी Rs 500 UPI वर पाठवा' },
  { label: 'Safe message', lang: 'en', text: 'Meeting at 5pm tomorrow bring the report thanks' },
]

const TICKER = ['Fake KYC expiry', 'UPI refund fraud', 'Part-time job fee scam', 'Lottery prize lure', 'Bank link phishing', 'Digital arrest threat']

function verdictStyle(v) {
  if (v === 'Scam') return { badge: 'bg-red-600', bar: 'bg-red-500', big: 'text-red-400' }
  if (v === 'Suspicious') return { badge: 'bg-amber-600', bar: 'bg-amber-500', big: 'text-amber-400' }
  return { badge: 'bg-emerald-600', bar: 'bg-emerald-500', big: 'text-emerald-400' }
}

export default function Home({ c, data, refresh }) {
  const { sched, trends, stats } = data
  const [msg, setMsg] = useState(SAMPLES[0].text)
  const [lang, setLang] = useState('auto')
  const [out, setOut] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('text')
  const fileRef = useRef(null)

  const trendRows = (trends?.trends ?? []).slice().sort((a, b) => b.count - a.count)
  const totalScans = stats?.total_scans ?? trendRows.reduce((n, r) => n + r.count, 0)
  const jobs = sched?.jobs ?? []
  const vs = out ? verdictStyle(out.verdict) : null

  const check = async () => {
    if (!msg.trim()) { setError('Paste a message first.'); return }
    setLoading(true); setError(''); setOut(null)
    try {
      setOut(await checkMessage(msg, lang === 'auto' ? null : lang))
      refresh()
    } catch { setError('Backend is not running. Start it with: uvicorn main:app --reload --port 8001') }
    finally { setLoading(false) }
  }

  const onImage = async (f) => {
    if (!f) return
    setLoading(true); setError(''); setOut(null)
    try {
      const j = await checkImage(f)
      if (j.ocr_text) setMsg(j.ocr_text)
      if (j.error) setError(j.error); else { setOut(j); refresh() }
    } catch { setError('Image check failed. Is tesseract installed?') }
    finally { setLoading(false) }
  }

  const speak = async () => {
    if (!out?.explanation) return
    if (!(await speakServerSide(out.explanation, out.lang))) speakBrowser(out.explanation, out.lang)
  }

  return (
    <>
      <section className="relative overflow-hidden">
        {c.dark && <div className="stars absolute inset-0 pointer-events-none" />}
        <div className="relative pt-12 pb-2 text-center">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight leading-[1.05]">
            Scam Shield, the AI guardian<br />for your messages
          </h1>
          <p className={`mt-4 text-sm md:text-base ${c.sub} max-w-xl mx-auto`}>
            Real-time scam detection in English, Hindi and Marathi. Paste any forward, get a verdict with reasons.
          </p>
          <div className="mt-6 flex justify-center gap-3 flex-wrap">
            <button onClick={() => document.getElementById('checker').scrollIntoView({ behavior: 'smooth' })} className="btn-primary px-7 py-2.5 text-sm">Scan my message</button>
            <a href="#/chat" className="btn-ghost px-7 py-2.5 text-sm">Ask the assistant</a>
          </div>
          <div className="relative mx-auto mt-10 w-fit">
            <div className="shield-glow absolute -inset-16" />
            <div className="shield mx-auto">
              <div className="shield-inner" />
              <div className="keyhole"><div className="hole-top" /><div className="hole-bottom" /></div>
            </div>
          </div>
        </div>
        {c.dark && (
          <div className="relative">
            <div className="horizon mx-auto max-w-4xl" />
            <div className="dotgrid h-16 max-w-4xl mx-auto -mt-2" />
          </div>
        )}
      </section>

      <div className={`border-y ${c.line} overflow-hidden mt-6`}>
        <div className="px-4 py-2.5 overflow-hidden">
          <div className={`ticker-track text-xs font-semibold tracking-widest ${c.sub}`}>
            {[...TICKER, ...TICKER].map((t, i) => <span key={i}>● {t.toUpperCase()}</span>)}
          </div>
        </div>
      </div>

      <section className="grid grid-cols-3 gap-4 mt-8 max-w-2xl mx-auto text-center">
        {[['87.5%', 'baseline accuracy'], [String(totalScans ?? '—'), 'scans analysed'], [`${stats?.threat_indicators ?? '—'}`, 'threat indicators']].map(([v, l]) => (
          <div key={l} className={`rounded-2xl border ${c.line} py-4`}>
            <p className="text-2xl font-bold">{v}</p>
            <p className={`text-xs ${c.sub}`}>{l}</p>
          </div>
        ))}
      </section>

      <section id="checker" className={`mt-8 ${c.panel} overflow-hidden`}>
        <div className="grid lg:grid-cols-2">
          <div className={`p-6 border-b lg:border-b-0 lg:border-r ${c.line}`}>
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex gap-2 text-sm">
                <button onClick={() => setTab('text')} className={`px-4 py-1.5 rounded-full ${tab === 'text' ? c.tabOn : c.tabOff}`}>Text</button>
                <button onClick={() => setTab('image')} className={`px-4 py-1.5 rounded-full ${tab === 'image' ? c.tabOn : c.tabOff}`}>Screenshot</button>
              </div>
              <select value={lang} onChange={e => setLang(e.target.value)} className="text-sm border rounded-full px-3 py-1.5 bg-transparent" style={{ borderColor: 'inherit' }}>
                <option value="auto">Auto</option><option value="en">English</option>
                <option value="hi">Hindi</option><option value="mr">Marathi</option>
              </select>
            </div>
            {tab === 'text' ? (
              <textarea value={msg} onChange={e => setMsg(e.target.value)} rows={7}
                placeholder="Paste the SMS or WhatsApp forward here…" className={c.input} />
            ) : (
              <div className={`mt-4 border border-dashed rounded-2xl p-8 text-center ${c.line}`}>
                <p className={`text-sm ${c.sub}`}>WhatsApp screenshot → OCR → same verdict.</p>
                <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={e => onImage(e.target.files[0])} />
                <button onClick={() => fileRef.current?.click()} className="btn-ghost px-5 py-2 mt-3 text-sm">Choose image</button>
              </div>
            )}
            <div className="mt-3 flex flex-wrap gap-2">
              {SAMPLES.map(s => (
                <button key={s.label} onClick={() => { setMsg(s.text); setLang(s.lang); setTab('text') }} className={c.chip}>{s.label}</button>
              ))}
            </div>
            <button onClick={check} disabled={loading} className="btn-primary w-full py-3 mt-4">{loading ? 'Analysing…' : 'Analyse now'}</button>
            {error && <p className="mt-3 text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-2xl p-3">{error}</p>}
            <p className={`text-xs mt-2 ${c.sub}`}>Scheduler: {sched?.running ? `live (${jobs.length} jobs)` : 'offline'} · <a className="underline" href="#/dashboard">open dashboard</a></p>
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
                <p className={`text-5xl font-bold ${c.dark ? 'text-white/10' : 'text-stone-200'}`}>?</p>
                <p className="mt-3 font-semibold">Verdict lands here</p>
                <p className={`mt-1 text-sm ${c.sub}`}>Score, triggers, links and what to do next.</p>
              </div>
            )}
            {!loading && out && !out.error && (
              <div className="rise">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className={`text-white text-sm font-bold px-4 py-1.5 rounded-full ${vs.badge}`}>{out.verdict}</span>
                  <span className={`text-3xl font-bold ${vs.big}`}>{(out.score * 100).toFixed(0)}%</span>
                  <span className={`text-xs ml-auto ${c.sub}`}>{out.category} · {out.lang?.toUpperCase()}</span>
                </div>
                <div className={`mt-3 h-2 rounded-full overflow-hidden ${c.track}`}>
                  <div className={`h-full ${vs.bar}`} style={{ width: `${Math.round(out.score * 100)}%` }} />
                </div>
                <p className="mt-4 text-sm leading-relaxed">{out.explanation}</p>
                <ul className="mt-3 space-y-1.5">
                  {(out.signals || []).slice(0, 3).map((s, i) => (
                    <li key={i} className="text-sm border-l-2 border-[#2f6bff] pl-3 opacity-90">{s}</li>
                  ))}
                </ul>
                {(out.model_tokens || []).length > 0 && (
                  <div className="mt-3">
                    <p className={`text-xs font-bold tracking-widest ${c.sub}`}>WHY THE MODEL VOTED {String(out.ml_label).toUpperCase()}</p>
                    <div className="mt-2 space-y-1.5">
                      {(out.model_tokens || []).slice(0, 5).map((t, i, arr) => {
                        const mx = Math.max(...arr.map(x => x.weight), 0.0001)
                        return (
                          <div key={i} className="grid grid-cols-12 items-center gap-2">
                            <span className="col-span-4 text-xs truncate">{t.token}</span>
                            <div className={`col-span-6 h-1.5 rounded-full overflow-hidden ${c.track}`}>
                              <div className="h-full bg-[#2f6bff] rounded-full" style={{ width: `${Math.max(6, Math.round((t.weight / mx) * 100))}%` }} />
                            </div>
                            <span className={`col-span-2 text-right text-xs font-mono ${c.sub}`}>{t.weight.toFixed(3)}</span>
                          </div>
                        )
                      })}
                    </div>
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
    </>
  )
}
