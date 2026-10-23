export default function About({ c }) {
  return (
    <div className="pt-8 max-w-4xl mx-auto">
      <h1 className="text-3xl md:text-4xl font-bold tracking-tight">How Scam Shield is built</h1>
      <p className={`text-sm mt-2 ${c.sub}`}>Hack-A-Throne 2026 · AI & Intelligent Systems · solo build · all code on GitHub.</p>

      <section className={`${c.panel} mt-6 p-6`}>
        <h2 className="font-bold">Privacy, safety & limitations</h2>
        <div className="mt-4 grid md:grid-cols-3 gap-4 text-sm">
          {[
            ['🔒 Privacy', [
              'Only SHA-256 of a message is stored — never the raw text.',
              'Phone numbers, emails and UPI IDs masked before display.',
              'Raw scans auto-purged after 24 hours by the scheduler.',
              'Trends dashboard reads hashed counts only.',
            ]],
            ['🛡️ Safety', [
              'Assistant redacts PII from every question before retrieval.',
              'Prompt-injection patterns rejected; answers cite only the 10 vetted docs.',
              'If no source supports an answer, it abstains instead of guessing.',
              'Rules + model fusion means one weak signal never alone flags a message.',
            ]],
            ['⚠️ Honest limits', [
              '65.8% on unseen hand-written messages — a baseline, not a guarantee.',
              'Screenshot OCR quality depends on image clarity and language pack.',
              'Rule-based layer can over-flag messages that merely contain links.',
              'No message ever replaces calling 1930 after real financial loss.',
            ]],
          ].map(([h, items]) => (
            <div key={h}>
              <p className="font-bold">{h}</p>
              <ul className="mt-2 space-y-1.5 opacity-80">
                {items.map(t => <li key={t}>• {t}</li>)}
              </ul>
            </div>
          ))}
        </div>
        <div className={`mt-4 pt-4 border-t text-sm ${c.line}`}>
          <span className="font-bold">Done →</span> <span className="opacity-80">offline PWA (installable, works without network) and WhatsApp forwarding of verdicts are live.</span>
          <span className="block mt-1"><span className="font-bold">Next →</span> <span className="opacity-80">MuRIL fine-tune to close the hand-written gap, WhatsApp bot onboarding, community trend sharing.</span></span>
        </div>
      </section>

      <section className="mt-6 rounded-[20px] bg-[#2f6bff] text-white p-6 flex flex-wrap items-center gap-4 justify-between" style={{ boxShadow: '0 0 50px rgba(47,107,255,.35)' }}>
        <p className="font-bold">Try it: check a forward, quiz yourself, or ask the assistant.</p>
        <div className="flex gap-3 flex-wrap">
          <a href="#/" className="bg-white text-blue-900 font-bold text-sm px-6 py-2.5 rounded-full">Check now</a>
          <a href="#/chat" className="border border-blue-200 text-sm px-6 py-2.5 rounded-full">Ask assistant</a>
          <a href="#/learn" className="border border-blue-200 text-sm px-6 py-2.5 rounded-full">Take the drill</a>
        </div>
      </section>

      <p className={`mt-6 mb-4 text-xs text-center ${c.sub}`}>
        Maintainer · <a className="underline" href="#/review">alert review queue</a> (admin)
      </p>
    </div>
  )
}
