import { useState } from 'react'
import { subscribeAlerts } from '../lib/api.js'

export default function Subscribe({ c }) {
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [consent, setConsent] = useState(false)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e?.preventDefault()
    setMsg(''); setErr('')
    const digits = phone.replace(/\D/g, '')
    if (digits.length < 10 || digits.length > 15) {
      setErr('Enter a WhatsApp number with country code (10-15 digits).')
      return
    }
    setBusy(true)
    try {
      const r = await subscribeAlerts(digits, name.trim(), consent)
      setMsg(`Subscribed${r.phone ? ` · ${r.phone}` : ''}. You will get occasional verified scam alerts. Reply STOP any time to unsubscribe.`)
      setPhone(''); setName(''); setConsent(false)
    } catch (e) {
      setErr(e.message || 'Subscription failed. Is the backend running?')
    } finally { setBusy(false) }
  }

  return (
    <div className="pt-8 max-w-xl mx-auto">
      <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Get scam alerts on WhatsApp</h1>
      <p className={`text-sm mt-2 ${c.sub}`}>
        New scam waves get verified by a human before anything is sent. No spam, no marketing — only safety alerts.
      </p>

      <form onSubmit={submit} className={`${c.panel} mt-6 p-6`}>
        <label className="block text-sm">
          Name (optional)
          <input value={name} onChange={e => setName(e.target.value)} maxLength={60}
            className={`mt-1 w-full border rounded-xl px-4 py-2.5 text-sm bg-transparent focus:outline-none focus:ring-2 focus:ring-[#2f6bff] ${c.line}`} />
        </label>

        <label className="block text-sm mt-4">
          WhatsApp number with country code
          <input value={phone} onChange={e => setPhone(e.target.value)} inputMode="tel"
            placeholder="91XXXXXXXXXX" autoComplete="tel"
            className={`mt-1 w-full border rounded-xl px-4 py-2.5 text-sm bg-transparent focus:outline-none focus:ring-2 focus:ring-[#2f6bff] ${c.line}`} />
        </label>

        <label className="flex items-start gap-2.5 text-sm mt-4">
          <input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} className="mt-0.5" />
          <span className={c.sub}>
            I agree to receive occasional scam-alert messages on WhatsApp. I can reply <b>STOP</b> at any time to unsubscribe.
          </span>
        </label>

        <button type="submit" disabled={!consent || !phone || busy}
          className="btn-primary w-full py-3 mt-5 disabled:opacity-40">
          {busy ? 'Subscribing…' : 'Subscribe to alerts'}
        </button>

        {msg && <p role="status" className="mt-3 text-sm text-emerald-500 bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-3">{msg}</p>}
        {err && <p role="alert" className="mt-3 text-sm text-red-400 bg-red-500/10 border border-red-500/30 rounded-xl p-3">{err}</p>}

        <p className={`text-xs mt-4 ${c.sub}`}>
          Consent is stored with date + source. Numbers are never shown publicly, and you can unsubscribe with
          STOP on WhatsApp or by asking us to remove you.
        </p>
      </form>

      <section className={`${c.panel} mt-4 p-5 text-sm`}>
        <p className="font-bold">How alerts work</p>
        <ol className={`mt-2 space-y-1.5 list-decimal list-inside ${c.sub}`}>
          <li>Threat feeds are collected every 6 hours into a review queue.</li>
          <li>A human verifies the campaign and writes the plain-language copy.</li>
          <li>Only approved alerts go out — via the official WhatsApp Cloud API.</li>
          <li>Reply STOP and you are removed immediately.</li>
        </ol>
      </section>
    </div>
  )
}
