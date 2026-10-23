import { useEffect, useRef, useState } from 'react'
import { checkMessage, assistantChat, assistantHealth } from '../lib/api.js'
import { QUICK, answer, fallback, shouldAnalyse, verdictSummary, detectLang } from '../lib/assistant.js'

const LS_KEY = 'scamshield-chat-v1'
const GREETING = 'Namaste! I am the Scam Shield assistant. Paste any suspicious message and I will analyse it, or ask me about KYC fraud, UPI safety, jobs, lottery or links.'

function loadSaved() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return [{ from: 'bot', text: GREETING, at: Date.now() }]
    const arr = JSON.parse(raw)
    return Array.isArray(arr) && arr.length ? arr : [{ from: 'bot', text: GREETING, at: Date.now() }]
  } catch { return [{ from: 'bot', text: GREETING, at: Date.now() }] }
}

function transcript(msgs) {
  return msgs.map(m => {
    const t = m.at ? new Date(m.at).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : ''
    const who = m.from === 'user' ? 'You' : 'Assistant'
    const badge = m.verdict ? ` [${m.verdict.verdict} ${(m.verdict.score * 100).toFixed(0)}% · ${m.verdict.category}]` : ''
    return `[${t}] ${who}${badge}: ${m.text}`
  }).join('\n')
}

export default function Chat({ c }) {
  const [msgs, setMsgs] = useState(loadSaved)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [copied, setCopied] = useState(false)
  const [ragOk, setRagOk] = useState(false)
  const bottom = useRef(null)
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs, busy])
  useEffect(() => {
    assistantHealth().then(h => setRagOk(h.enabled && h.retrieval === 'ok')).catch(() => setRagOk(false))
  }, [])
  useEffect(() => {
    try { localStorage.setItem(LS_KEY, JSON.stringify(msgs.slice(-200))) } catch { /* full/blocked */ }
  }, [msgs])

  const push = (m) => setMsgs(prev => [...prev, { at: Date.now(), ...m }])

  const download = () => {
    const blob = new Blob([`Scam Shield — assistant transcript\nExported ${new Date().toLocaleString('en-IN')}\n\n${transcript(msgs)}\n`], { type: 'text/plain' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'scam-shield-chat.txt'
    a.click()
    URL.revokeObjectURL(a.href)
  }

  const copyAll = async () => {
    try {
      await navigator.clipboard.writeText(transcript(msgs))
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch { /* clipboard blocked */ }
  }

  const clearAll = () => {
    if (!window.confirm('Delete this chat history from this browser?')) return
    localStorage.removeItem(LS_KEY)
    setMsgs([{ from: 'bot', text: GREETING, at: Date.now() }])
  }

  const send = async (raw) => {
    const text = (raw ?? input).trim()
    if (!text || busy) return
    setInput('')
    push({ from: 'user', text })
    setBusy(true)
    // 1) Prefer the grounded RAG assistant (cited, server-verdict). Fall back to local brain.
    if (ragOk && !/^check a message$/i.test(text)) {
      try {
        const hist = msgs.slice(-6).map(m => ({ role: m.from === 'user' ? 'user' : 'assistant', text: m.text.slice(0, 500) }))
        const r = await assistantChat(text, shouldAnalyse(text) ? text : '', detectLang(text), hist)
        push({
          from: 'bot', text: r.answer, citations: r.citations || [],
          evidence: r.evidence_status, verdict: r.verdict && r.verdict.verdict ? {
            verdict: r.verdict.verdict,
            score: r.verdict.score ?? 0,
            category: r.verdict.category || '',
          } : null,
          generator: r.generator,
          safety: r.safety_notice,
          abstained: r.abstained,
        })
        setBusy(false)
        return
      } catch { /* fall through to local brain */ }
    }
    try {
      if (/^check a message$/i.test(text)) {
        await new Promise(r => setTimeout(r, 300))
        push({ from: 'bot', text: 'Paste the suspicious SMS or WhatsApp forward below and I will analyse it right away.' })
      } else if (shouldAnalyse(text)) {
        push({ from: 'bot', text: 'Analysing your message…' })
        const j = await checkMessage(text)
        setMsgs(prev => [...prev.slice(0, -1), {
          from: 'bot', verdict: j, text: verdictSummary(j),
        }])
      } else {
        const direct = answer(text)
        await new Promise(r => setTimeout(r, 350))
        push({ from: 'bot', text: direct || fallback(detectLang(text)) })
      }
    } catch {
      push({ from: 'bot', text: 'Backend is offline — start it on :8001 and try again. For urgent fraud, call 1930.' })
      setMsgs(prev => {
        const last = prev[prev.length - 1]
        if (last?.text === 'Analysing your message…') return prev.slice(0, -1)
        return prev
      })
    } finally { setBusy(false) }
  }

  return (
    <div className="pt-8 max-w-3xl mx-auto">
      <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-center">Ask the assistant</h1>
      <p className={`text-sm mt-2 text-center ${c.sub}`}>Safety Q&A plus one-tap message analysis. Works in English, Hindi and Marathi.</p>
      <p className={`text-xs mt-1 text-center ${c.sub}`}>{ragOk ? 'Grounded mode: answers cite trusted sources.' : 'Offline mode: local safety brain (start backend for cited answers).'}</p>
      <div className="mt-3 flex items-center justify-center gap-2 flex-wrap">
        <span className={`text-xs ${c.sub}`}>{msgs.length} messages saved in this browser</span>
        <button onClick={download} className="btn-ghost text-xs px-3.5 py-1.5">Download .txt</button>
        <button onClick={copyAll} className="btn-ghost text-xs px-3.5 py-1.5">{copied ? 'Copied!' : 'Copy all'}</button>
        <button onClick={clearAll} className="btn-ghost text-xs px-3.5 py-1.5">Clear</button>
      </div>

      <div className={`${c.panel} mt-6 p-4 md:p-5`}>
        <div className="h-[46vh] overflow-y-auto space-y-3 pr-1">
          {msgs.map((m, i) => (
            <div key={i} className={`flex ${m.from === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${m.from === 'user' ? 'bg-[#2f6bff] text-white' : c.dark ? 'bg-white/5 border border-white/10' : 'bg-stone-100 border border-stone-200'}`}>
                {m.verdict && (
                  <span className={`inline-block text-xs font-bold px-2.5 py-0.5 rounded-full text-white mb-1.5 ${m.verdict.verdict === 'Scam' ? 'bg-red-600' : m.verdict.verdict === 'Suspicious' ? 'bg-amber-600' : 'bg-emerald-600'}`}>
                    {m.verdict.verdict} {(m.verdict.score * 100).toFixed(0)}%
                  </span>
                )}
                <p className="whitespace-pre-line">{m.text}</p>
                {m.evidence && (
                  <p className="mt-1.5 text-xs opacity-70 flex items-center gap-2 flex-wrap">
                    <span>Evidence: {m.evidence}</span>
                    {m.generator && (
                      <span className="px-1.5 py-0.5 rounded border border-[#2f6bff]/40 text-[#7ea2ff]">
                        {m.generator === 'hosted' ? 'LLM' : 'Offline mode'}
                      </span>
                    )}
                  </p>
                )}
                {m.abstained && (
                  <p className="mt-1.5 text-xs text-amber-400">
                    ⚠ Not enough trusted evidence — this answer is not grounded in a source.
                  </p>
                )}
                {(m.citations || []).length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {(m.citations || []).map(ci => (
                      <a key={ci.id} href={ci.url} target="_blank" rel="noreferrer"
                        title={ci.passage ? `${ci.title} — ${ci.passage.slice(0, 160)}` : ci.title}
                        className="text-xs px-2 py-0.5 rounded-full border border-[#2f6bff]/50 text-[#7ea2ff]">
                        [{ci.id}] {ci.title.slice(0, 28)}
                      </a>
                    ))}
                  </div>
                )}
                {m.safety && (
                  <p className="mt-1.5 text-[11px] opacity-70 border-l-2 border-amber-500/70 pl-2">{m.safety}</p>
                )}
                {m.verdict && (
                  <a href="#/" className="underline text-xs opacity-80">Open full analysis on Home →</a>
                )}
              </div>
            </div>
          ))}
          {busy && <p className={`text-xs ${c.sub}`}>Assistant is typing…</p>}
          <div ref={bottom} />
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {QUICK.map(q => (
            <button key={q} onClick={() => send(q)} className={c.chip}>{q}</button>
          ))}
        </div>

        <div className="mt-3 flex gap-2">
          <input value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder="Type a question or paste a message…"
            className={`flex-1 border rounded-full px-4 py-2.5 text-sm bg-transparent focus:outline-none focus:ring-2 focus:ring-[#2f6bff] ${c.line}`} />
          <button onClick={() => send()} disabled={busy} className="btn-primary px-6 py-2.5 text-sm">Send</button>
        </div>
      </div>
    </div>
  )
}
