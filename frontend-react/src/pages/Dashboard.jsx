const JOB_META = {
  threat_refresh: 'Threat intel · 6h',
  trends: 'Trend digest · hourly',
  purge: 'Privacy purge · daily',
  tip: 'Safety tip · 09:00',
  standup: 'Standup nudge · 21:05',
}

export default function Dashboard({ c, data, refresh }) {
  const { sched, trends, alerts, history, stats } = data
  const trendRows = (trends?.trends ?? []).slice().sort((a, b) => b.count - a.count).slice(0, 8)
  const maxCount = Math.max(1, ...trendRows.map(r => r.count))
  const jobs = sched?.jobs ?? []
  const byVerdict = stats?.by_verdict ?? {}
  const total = stats?.total_scans ?? 0

  return (
    <div className="pt-8">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Live intel dashboard</h1>
          <p className={`text-sm mt-1 ${c.sub}`}>Scheduler-fed, anonymised, auto-refreshing. No message text stored.</p>
        </div>
        <button onClick={refresh} className="btn-ghost text-sm px-5 py-2">Refresh</button>
      </div>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        {[[String(total), 'total scans'], [String(byVerdict.Scam ?? 0), 'flagged scam'], [String(stats?.threat_indicators ?? 0), 'threat indicators'], [`${jobs.length || 0}/5`, 'jobs live']].map(([v, l]) => (
          <div key={l} className={`${c.panel} p-4 text-center`}>
            <p className="text-2xl font-bold">{v}</p>
            <p className={`text-xs ${c.sub}`}>{l}</p>
          </div>
        ))}
      </section>

      <section className="mt-6 grid lg:grid-cols-3 gap-6">
        <div className={`lg:col-span-2 ${c.panel} p-6`}>
          <div className="flex items-baseline justify-between">
            <h2 className="text-xl font-bold">What scammers are trying today</h2>
            <span className={`text-xs ${c.sub}`}>hourly · anonymised</span>
          </div>
          <div className="mt-5 space-y-4">
            {trendRows.length === 0 && <p className={`text-sm ${c.sub}`}>Run a few checks to fill this.</p>}
            {trendRows.map((r, i) => (
              <div key={i} className="grid grid-cols-12 items-center gap-3">
                <span className="col-span-4 text-sm font-medium truncate">{r.category} <span className={`text-xs ${c.sub}`}>{r.date}</span></span>
                <div className={`col-span-6 h-2.5 rounded-full overflow-hidden ${c.track}`}>
                  <div className="h-full bg-[#2f6bff] rounded-full" style={{ width: `${Math.round((r.count / maxCount) * 100)}%`, boxShadow: '0 0 10px rgba(47,107,255,.7)' }} />
                </div>
                <span className="col-span-2 text-right font-mono font-bold text-sm">{r.count}</span>
              </div>
            ))}
          </div>
          <div className={`mt-6 pt-4 border-t ${c.line}`}>
            <p className={`text-xs font-bold tracking-widest ${c.sub}`}>RECENT CHECKS · ANONYMISED</p>
            <div className="mt-2 space-y-1.5">
              {((history?.history) ?? []).length === 0 && <p className={`text-sm ${c.sub}`}>No checks yet.</p>}
              {((history?.history) ?? []).map((h, i) => (
                <div key={i} className="flex items-center gap-2.5 text-sm">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${h.verdict === 'Scam' ? 'bg-red-500' : h.verdict === 'Suspicious' ? 'bg-amber-500' : 'bg-emerald-500'}`} />
                  <span className="font-medium">{h.verdict}</span>
                  <span className={`truncate ${c.sub}`}>{h.category} · {String(h.lang).toUpperCase()} · {(h.score * 100).toFixed(0)}%</span>
                  <span className={`ml-auto text-xs font-mono shrink-0 ${c.sub}`}>{String(h.created_at).slice(5, 16)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className={`${c.panel} p-5`}>
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm tracking-widest">SCHEDULER JOBS</h3>
              <span className={`text-xs font-bold ${sched?.running ? 'text-emerald-500' : 'text-amber-500'}`}>{sched?.running ? '● LIVE' : '○ OFFLINE'}</span>
            </div>
            <div className="mt-2 space-y-2">
              {jobs.map(j => (
                <div key={j.id} className="flex justify-between text-sm gap-2">
                  <span className="opacity-80">{JOB_META[j.id] ?? j.id}</span>
                  <span className="font-mono text-xs shrink-0">{j.next ? new Date(j.next).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'}</span>
                </div>
              ))}
              {jobs.length === 0 && <p className={`text-sm ${c.sub}`}>Backend offline. Start it on :8001.</p>}
            </div>
          </div>
          <div className={`${c.panel} p-5`}>
            <h3 className="font-bold text-sm tracking-widest">SAFETY NOTES</h3>
            <ul className="mt-2 space-y-2 text-sm opacity-80 max-h-56 overflow-auto">
              {(alerts?.alerts ?? []).slice(-6).reverse().map((a, i) => <li key={i} className="border-l-2 border-[#2f6bff] pl-2">{String(a).slice(0, 120)}</li>)}
              {(!alerts?.alerts?.length) && <li>First note appears after a check.</li>}
            </ul>
            <p className={`mt-3 text-xs ${c.sub}`}>Same feed that ships to WhatsApp in production.</p>
          </div>
        </div>
      </section>
    </div>
  )
}
