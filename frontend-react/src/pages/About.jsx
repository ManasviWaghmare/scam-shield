const ARCH = `User ──paste/screenshot──▶ React ──POST /check──▶ FastAPI :8001
mask PII ──▶ [ML prob + rules risk] ──fuse──▶ Safe / Suspicious / Scam
hash(msg) stored ──hourly──▶ /trends ──▶ dashboard bars
scheduler ──6h──▶ threat_cache ──▶ hotter verdicts
scheduler ──9:00/21:05──▶ outbox ──▶ /alerts ──▶ WhatsApp/Telegram
Chat ──POST /assistant/chat──▶ TF-IDF retrieve (10 docs) ──▶ cited answer`;

const STACK = [
  ['API', 'FastAPI + uvicorn — 12 endpoints on :8001'],
  ['Assistant', 'TrustRAG-lite: TF-IDF retrieval over 10 curated docs, validated citations, hosted-LLM optional'],
  ['Scheduler', 'APScheduler — 5 jobs, Asia/Kolkata'],
  ['AI', 'TF-IDF + LogReg 87.5% (MuRIL opt-in via SCAMSHIELD_MODEL)'],
  ['Rules', 'URLs, urgency, OTP/PIN, KYC/job/lottery patterns'],
  ['Explain', 'Token weights + EN/HI/MR templates + voice'],
  ['OCR', 'Tesseract eng+hin+mar for screenshots'],
  ['Data', 'SQLite, hash-only, 24h purge; 166-row trilingual set'],
  ['Tests', '20/20 green: pipeline, RAG, citations, safety, regression'],
  ['Notify', 'CallMeBot + Telegram + outbox fallback'],
  ['Web', 'React 18 + Vite + Tailwind, dark HEXLY theme'],
]

export default function About({ c }) {
  return (
    <div className="pt-8 max-w-4xl mx-auto">
      <h1 className="text-3xl md:text-4xl font-bold tracking-tight">How Scam Shield is built</h1>
      <p className={`text-sm mt-2 ${c.sub}`}>Hack-A-Throne 2026 · AI & Intelligent Systems · solo build · all code on GitHub.</p>

      <section className={`${c.panel} mt-6 p-6`}>
        <h2 className="font-bold">Architecture</h2>
        <pre className={`mt-3 text-xs leading-relaxed overflow-x-auto p-4 rounded-2xl ${c.dark ? 'bg-black/40' : 'bg-stone-100'}`}>{ARCH}</pre>
        <div className="mt-4 space-y-2 text-sm">
          {[['Check →', 'message or screenshot in, verdict plus score, category, triggers and action out in under 300 ms.'], ['Score →', '0.6 model plus 0.4 rules; strong explicit signals force Scam.'], ['Protect →', 'threat cache refreshes every 6 hours, trends hourly, raw text purged daily.']].map(([h, b]) => (
            <p key={h}><span className="font-bold">{h}</span> <span className="opacity-80">{b}</span></p>
          ))}
          <p><span className="font-bold">Ask →</span> <span className="opacity-80">assistant explains any verdict with cited trusted sources, or abstains honestly.</span></p>
        </div>
      </section>

      <section className={`${c.panel} mt-6 p-6`}>
        <h2 className="font-bold">Technology stack</h2>
        <div className="mt-3 divide-y" style={{ borderColor: 'inherit' }}>
          {STACK.map(([k, v]) => (
            <div key={k} className={`grid grid-cols-12 gap-3 py-2 border-b ${c.line} text-sm`}>
              <span className="col-span-3 font-bold">{k}</span>
              <span className="col-span-9 opacity-80">{v}</span>
            </div>
          ))}
        </div>
      </section>

      <section className={`${c.panel} mt-6 p-6`}>
        <h2 className="font-bold">Honest metrics</h2>
        <ul className="mt-3 space-y-2 text-sm opacity-90">
          <li><b>87.5%</b> on the 38 hand-written messages — the headline number.</li>
          <li><b>100%</b> on the 166 template-expanded split — optimistic (same-template leakage).</li>
          <li><b>65.8%</b> training only on templates, testing on hand-written — the gap MuRIL must close.</li>
          <li><b>20/20</b> unit tests green (pipeline + RAG + citations + safety) · <b>276</b> live threat indicators synced.</li>
          <li><b>10</b> curated sources power grounded assistant answers — or it abstains honestly.</li>
        </ul>
      </section>

      <section className="mt-6 rounded-[20px] bg-[#2f6bff] text-white p-6 flex flex-wrap items-center gap-4 justify-between" style={{ boxShadow: '0 0 50px rgba(47,107,255,.35)' }}>
        <p className="font-bold">Try it: check a forward, quiz yourself, or ask the assistant.</p>
        <div className="flex gap-3 flex-wrap">
          <a href="#/" className="bg-white text-blue-900 font-bold text-sm px-6 py-2.5 rounded-full">Check now</a>
          <a href="#/chat" className="border border-blue-200 text-sm px-6 py-2.5 rounded-full">Ask assistant</a>
          <a href="#/learn" className="border border-blue-200 text-sm px-6 py-2.5 rounded-full">Take the drill</a>
        </div>
      </section>
    </div>
  )
}
