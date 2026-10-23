import { useEffect, useState } from 'react'
import { pendingAlerts, approveAlert, sendApprovedAlerts } from '../lib/api.js'

const DEFAULT_ACTION = 'Do not click links or share OTPs. Verify at cybercrime.gov.in or call 1930.'

export default function Review({ c }) {
  const [adminKey, setAdminKey] = useState(() => sessionStorage.getItem('scamshield-admin-key') || '')
  const [items, setItems] = useState([])
  const [drafts, setDrafts] = useState({})
  const [status, setStatus] = useState({ type: '', text: '' })
  const [busy, setBusy] = useState(false)
  const [sending, setSending] = useState(false)

  const load = async (key = adminKey) => {
    setBusy(true)
    try {
      const r = await pendingAlerts(key)
      setItems(r.pending || [])
      setStatus({ type: 'ok', text: `${r.awaiting_review ?? 0} awaiting review · ${r.total ?? 0} total in queue` })
    } catch (e) {
      setStatus({ type: 'err', text: e.message })
    } finally { setBusy(false) }
  }

  useEffect(() => { load() }, [])

  const draft = (item) => drafts[item.id] || {
    how: item.how_it_works || '',
    action: item.action || DEFAULT_ACTION,
  }
  const setDraft = (id, patch) => setDrafts(d => {
    const item = items.find(x => x.id === id)
    const base = d[id] || { how: item?.how_it_works || '', action: item?.action || DEFAULT_ACTION }
    return { ...d, [id]: { ...base, ...patch } }
  })

  const approve = async (item) => {
    const d = draft(item)
    if (!d.how.trim() || !d.action.trim()) {
      setStatus({ type: 'err', text: 'Fill both fields before approving.' })
      return
    }
    try {
      await approveAlert({ url: item.id, how_it_works: d.how, action: d.action }, adminKey)
      setItems(prev => prev.filter(x => x.id !== item.id))
      setStatus({ type: 'ok', text: 'Approved. It will go out on the next send.' })
    } catch (e) {
      setStatus({ type: 'err', text: e.message })
    }
  }

  const sendNow = async () => {
    setSending(true)
    try {
      const r = await sendApprovedAlerts(adminKey)
      setStatus({ type: 'ok', text: `Sent ${r.sent || 0} · queued ${r.queued || 0} · failed ${r.failed || 0} (${r.subscribers || 0} active subscribers)` })
    } catch (e) {
      setStatus({ type: 'err', text: e.message })
    } finally { setSending(false) }
  }

  return (
    <div className="pt-8 max-w-3xl mx-auto">
      <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Alert review queue</h1>
      <p className={`text-sm mt-2 ${c.sub}`}>
        Human gate: nothing reaches a phone until you write the copy and approve it.
      </p>

      <div className={`${c.panel} mt-5 p-4 flex flex-wrap items-end gap-3`}>
        <label className="text-sm flex-1 min-w-[220px]">
          Admin key <span className={`text-xs ${c.sub}`}>(only if ADMIN_KEY is set on the server)</span>
          <input type="password" value={adminKey}
            onChange={e => { setAdminKey(e.target.value); sessionStorage.setItem('scamshield-admin-key', e.target.value) }}
            placeholder="X-Admin-Key"
            className={`mt-1 w-full border rounded-xl px-3 py-2 text-sm bg-transparent ${c.line}`} />
        </label>
        <button onClick={() => load()} disabled={busy} className="btn-ghost text-sm px-4 py-2">
          {busy ? 'Loading…' : 'Reload queue'}
        </button>
        <button onClick={sendNow} disabled={sending} className="btn-primary text-sm px-4 py-2">
          {sending ? 'Sending…' : 'Send approved'}
        </button>
      </div>

      {status.text && (
        <p role="status" className={`mt-3 text-sm rounded-xl border p-3 ${status.type === 'err'
          ? 'text-red-400 bg-red-500/10 border-red-500/30'
          : 'text-emerald-500 bg-emerald-500/10 border-emerald-500/30'}`}>
          {status.text}
        </p>
      )}

      {!busy && items.length === 0 && (
        <div className={`${c.panel} mt-4 p-8 text-center text-sm ${c.sub}`}>
          Queue is empty. Run <code>python alert_pipeline.py collect</code> or POST <code>/alerts/collect</code> to fetch new threats.
        </div>
      )}

      <div className="mt-4 space-y-4">
        {items.map(item => {
          const d = draft(item)
          return (
            <article key={item.id} className={`${c.panel} p-5`}>
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div>
                  <p className="font-bold text-sm">{item.title}</p>
                  <p className={`text-xs mt-1 ${c.sub}`}>
                    {item.scam_type} · added {item.added_at?.replace('T', ' ')}
                  </p>
                </div>
                <a href={item.source_url} target="_blank" rel="noreferrer"
                  className={`text-xs underline ${c.sub}`}>source ↗</a>
              </div>

              <label className="block text-xs mt-3 font-semibold">How it works
                <textarea rows={2} value={d.how}
                  onChange={e => setDraft(item.id, { how: e.target.value })}
                  className={`mt-1 w-full border rounded-xl p-3 text-sm bg-transparent focus:outline-none focus:ring-2 focus:ring-[#2f6bff] ${c.line}`} />
              </label>
              <label className="block text-xs mt-2 font-semibold">Safety action
                <textarea rows={2} value={d.action}
                  onChange={e => setDraft(item.id, { action: e.target.value })}
                  className={`mt-1 w-full border rounded-xl p-3 text-sm bg-transparent focus:outline-none focus:ring-2 focus:ring-[#2f6bff] ${c.line}`} />
              </label>

              <div className="mt-3 flex items-center gap-3">
                <button onClick={() => approve(item)} className="btn-primary text-sm px-4 py-2">Approve</button>
                <span className={`text-xs ${c.sub}`}>Approve ≠ send — use “Send approved” above.</span>
              </div>
            </article>
          )
        })}
      </div>
    </div>
  )
}
