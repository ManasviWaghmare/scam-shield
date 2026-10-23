import { useState } from 'react'

const SCAMS = [
  { name: 'Fake KYC expiry', example: '"SBI KYC expired, verify at sbi-kyc-update.xyz in 24 hrs"', signs: ['Urgency: 24 hours, blocked', 'Link with odd ending (.xyz)', 'Bank never uses SMS links'], lang: 'EN · HI · MR' },
  { name: 'UPI refund / OTP harvest', example: '"Refund of Rs 4,999 pending, share UPI PIN"', signs: ['Asks PIN/OTP to RECEIVE money', 'You never need a PIN to get paid', 'Collector request outside your app'], lang: 'EN · HI · MR' },
  { name: 'Advance-fee job', example: '"Earn Rs 3,000/day from home, pay Rs 500 joining fee"', signs: ['Fee before first salary', 'Telegram task + UPI payment', 'No interview, no offer letter'], lang: 'EN · HI · MR' },
  { name: 'Lottery prize', example: '"You won Rs 50,000! Pay Rs 99 claim fee at prize-claim.top"', signs: ['Won without entering', 'Fee/tax/OTP to release prize', 'Shortened claim link'], lang: 'EN · HI' },
  { name: 'Phishing link', example: '"Track parcel: bit.ly/3xKyc9"', signs: ['Shortener hides the site', 'Long link with @ or many dashes', 'Mismatched brand domain'], lang: 'EN' },
  { name: 'Digital arrest', example: '"Your son is in custody, send Rs 20,000 now"', signs: ['Panic + secrecy demand', 'No real officer takes UPI fines', 'Verify via 1930 first'], lang: 'EN · HI' },
]

const QUIZ = [
  { q: 'A SMS says KYC expired with a link. What do you do?', options: ['Tap and enter details fast', 'Ignore the link, verify via official app', 'Forward OTP to the sender'], answer: 1, why: 'Banks never update KYC over SMS links. Always verify in the official app.' },
  { q: 'Someone offers a refund but asks your UPI PIN. Correct?', options: ['Yes, PIN is needed to receive', 'No — PIN is only for paying', 'Share OTP instead'], answer: 1, why: 'Receiving money never needs a PIN. Any such ask is fraud.' },
  { q: 'You won a lottery you never entered. Fee Rs 99 to claim?', options: ['Pay fast before expiry', 'It is a scam — delete and report', 'Share with friends first'], answer: 1, why: 'Unentered wins plus a release fee is the classic lottery lure.' },
]

export default function Learn({ c }) {
  const [qi, setQi] = useState(0)
  const [picked, setPicked] = useState(null)
  const [score, setScore] = useState(0)
  const [done, setDone] = useState(false)
  const q = QUIZ[qi]

  const pick = (i) => {
    if (picked !== null) return
    setPicked(i)
    if (i === q.answer) setScore(s => s + 1)
  }
  const next = () => {
    if (qi + 1 >= QUIZ.length) setDone(true)
    else { setQi(qi + 1); setPicked(null) }
  }

  return (
    <div className="pt-8">
      <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Learn the five traps</h1>
      <p className={`text-sm mt-2 ${c.sub}`}>Real patterns from the dataset, with examples in your language. Then test yourself.</p>

      <section className="grid md:grid-cols-2 gap-5 mt-6">
        {SCAMS.map(s => (
          <div key={s.name} className={`${c.panel} p-5`}>
            <div className="flex items-center justify-between gap-2">
              <h2 className="font-bold">{s.name}</h2>
              <span className={`text-xs ${c.sub}`}>{s.lang}</span>
            </div>
            <p className={`mt-2 text-sm italic opacity-90`}>{s.example}</p>
            <ul className="mt-3 space-y-1.5">
              {s.signs.map((g, i) => <li key={i} className="text-sm border-l-2 border-[#2f6bff] pl-2.5 opacity-90">{g}</li>)}
            </ul>
          </div>
        ))}
      </section>

      <section className={`mt-8 ${c.panel} p-6`}>
        <h2 className="text-xl font-bold">3-question safety drill</h2>
        {!done ? (
          <div className="mt-4">
            <p className={`text-xs font-bold tracking-widest ${c.sub}`}>QUESTION {qi + 1} OF {QUIZ.length} · SCORE {score}</p>
            <p className="mt-2 font-semibold">{q.q}</p>
            <div className="mt-3 space-y-2">
              {q.options.map((o, i) => (
                <button key={i} onClick={() => pick(i)} disabled={picked !== null}
                  className={`w-full text-left text-sm px-4 py-2.5 rounded-2xl border ${picked === null ? c.tabOff : i === q.answer ? 'border-emerald-500 bg-emerald-500/10' : i === picked ? 'border-red-500 bg-red-500/10' : c.tabOff}`}>
                  {o}
                </button>
              ))}
            </div>
            {picked !== null && (
              <div className="mt-3 flex items-center gap-3 flex-wrap">
                <p className="text-sm">{picked === q.answer ? 'Correct. ' : 'Not quite. '}{q.why}</p>
                <button onClick={next} className="btn-primary text-sm px-5 py-2">{qi + 1 >= QUIZ.length ? 'See score' : 'Next'}</button>
              </div>
            )}
          </div>
        ) : (
          <div className="mt-4 text-center py-4">
            <p className="text-4xl font-bold">{score}/{QUIZ.length}</p>
            <p className={`text-sm mt-1 ${c.sub}`}>{score === 3 ? 'Scam-proof. Teach one elder today.' : 'Good start — replay the traps above, then retry.'}</p>
            <button onClick={() => { setQi(0); setPicked(null); setScore(0); setDone(false) }} className="btn-ghost text-sm px-5 py-2 mt-3">Retry drill</button>
          </div>
        )}
      </section>
    </div>
  )
}
