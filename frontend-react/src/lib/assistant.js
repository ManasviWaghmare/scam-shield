// Rule-based safety assistant. Offline, trilingual keywords.
// Long non-question messages are treated as suspect texts and analysed via /check.

export const QUICK = ['Check a message', 'What is KYC fraud?', 'UPI safety rules', 'Call 1930', 'How does this work?']

const has = (t, words) => words.some(w => t.includes(w))

export function detectLang(t) {
  if (/[\u0900-\u097F]/.test(t)) {
    if (['आहे', 'नाही', 'तुम्ही', 'करू', 'काय'].some(w => t.includes(w))) return 'mr'
    return 'hi'
  }
  return 'en'
}

const A = {
  en: {
    hello: 'Namaste! I am the Scam Shield assistant. Paste any suspicious message and I will analyse it, or ask me about KYC fraud, UPI safety, jobs, lottery or links.',
    kyc: 'KYC fraud: fake SMS says your bank KYC expired with a link. Banks never update KYC over SMS links. Signs: urgency (24 hours, blocked), shortened link, odd domain like .xyz. Never click — call 1930.',
    upi: 'UPI safety rules:\n1. You never need a PIN to RECEIVE money.\n2. Any refund asking your UPI PIN, OTP or CVV is fraud.\n3. Keep your PIN secret — banks never ask it on call.\n4. Verify collect requests only inside your own UPI app.',
    job: 'Job scam: part-time offers promising daily income that ask a joining or training fee first. Real employers never charge to hire you. Asking fees on UPI or Telegram tasks is a red flag.',
    lottery: 'Lottery scam: you cannot win a lottery you never entered. Claim fees, taxes or OTP to release a prize always mean fraud. Delete and report it.',
    link: 'Link check: hover before tapping. Danger signs: URL shorteners hiding the site, odd endings (.xyz, .top), very long links, @ symbols. Paste it here and I will score it.',
    helpline: 'If money is involved act fast: call 1930 now, then file at cybercrime.gov.in with screenshots. Every minute matters for freezing fraud accounts.',
    how: 'How Scam Shield works:\n1. AI model scores your message in English, Hindi or Marathi.\n2. Rules add risk for links, urgency words and OTP asks.\n3. You get Safe, Suspicious or Scam with exact reasons.\n4. A scheduler refreshes threat lists every 6 hours.',
    model: 'The detector blends a language model (87.5% baseline, MuRIL upgrade planned) with rule checks. Scores: below 40 Safe, 40 to 70 Suspicious, above 70 Scam.',
    privacy: 'Privacy first: your message is never stored. Only an anonymous hash plus the verdict is kept for 24 hours, then purged automatically.',
    fallback: 'I can analyse suspicious messages or explain KYC, UPI, job, lottery and link scams. Try pasting the message, or tap a suggestion below.',
    analysing: 'Analysing your message…',
  },
  hi: {
    hello: 'नमस्ते! मैं Scam Shield सहायक हूँ। कोई संदिग्ध संदेश भेजें, मैं जांच करूँगा।',
    kyc: 'KYC धोखाधड़ी: बैंक कभी SMS लिंक से KYC अपडेट नहीं कराता। तुरंत, बंद, 24 घंटे जैसे शब्द + छोटा लिंक = खतरा। क्लिक न करें, 1930 पर कॉल करें।',
    upi: 'UPI नियम:\n1. पैसे पाने के लिए PIN नहीं चाहिए।\n2. रिफंड के नाम पर OTP/PIN मांगे तो धोखा है।\n3. PIN कभी किसी को न बताएं।',
    helpline: 'पैसे का मामला हो तो तुरंत 1930 पर कॉल करें, फिर cybercrime.gov.in पर रिपोर्ट करें।',
    fallback: 'संदिग्ध संदेश भेजें या KYC, UPI, नौकरी, लॉटरी के बारे में पूछें।',
  },
  mr: {
    hello: 'नमस्कार! मी Scam Shield सहाय्यक आहे. संशयास्पद संदेश पाठवा, मी तपासतो.',
    kyc: 'KYC फसवणूक: बँक SMS लिंकवरून KYC अपडेट करत नाही. तात्काळ, बंद + छोटी लिंक = धोका. 1930 ला कॉल करा.',
    upi: 'UPI नियम:\n1. पैसे मिळवण्यासाठी PIN लागत नाही।\n2. OTP/PIN मागितला तर फसवणूक आहे।\n3. PIN कोणालाही सांगू नका।',
    helpline: 'पैशांचा विषय असेल तर लगेच 1930 ला कॉल करा, मग cybercrime.gov.in वर तक्रार करा.',
    fallback: 'संशयास्पद संदेश पाठवा किंवा KYC, UPI, नोकरी, लॉटरीबद्दल विचारा.',
  },
}

export function answer(text) {
  const t = text.toLowerCase()
  const lang = detectLang(text)
  const L = A[lang] || A.en
  const E = A.en
  if (/\b(hello|hi+|hey+|namaste|namaskar)\b/.test(t) || has(t, ['नमस्ते', 'नमस्कार'])) return L.hello || E.hello
  if (has(t, ['kyc', 'केवायसी', 'kewaysi'])) return L.kyc || E.kyc
  if (has(t, ['upi', 'otp', 'pin', 'refund', 'रिफंड', 'ओटीपी', 'पिन'])) return L.upi || E.upi
  if (has(t, ['job', 'नौकरी', 'नोकरी', 'part-time', 'earning'])) return E.job
  if (has(t, ['lottery', 'prize', 'लॉटरी', 'इनाम', 'winner'])) return E.lottery
  if (has(t, ['link', 'url', 'bit.ly', 'http', 'लिंक'])) return E.link
  if (has(t, ['1930', 'report', 'complaint', 'helpline', 'रिपोर्ट', 'तक्रार', 'call'])) return L.helpline || E.helpline
  if (/\bhow\b|\bkaise\b/.test(t) || has(t, ['work', 'कैसे', 'कसे'])) return E.how
  if (has(t, ['model', 'accuracy', 'ai'])) return E.model
  if (has(t, ['privacy', 'store', 'data', 'private'])) return E.privacy
  return null // caller falls back / analyses
}

export function fallback(lang) {
  return (A[lang] || A.en).fallback
}

export function shouldAnalyse(text) {
  const t = text.trim()
  const low = t.toLowerCase()
  // Any link is always worth scoring.
  if (/https?:\/\/|www\.|bit\.ly|t\.me\/|\.xyz|\.top/.test(low)) return true
  if (t.length < 25) return false
  if (/\?$/.test(t)) return false
  // Question-led texts go to Q&A even when long.
  if (/^(what|how|why|is|are|can|should|क्या|काय|explain|tell me)\b/.test(low)) return false
  if (has(low, ['what', 'how', 'why', 'क्या', 'काय', 'explain', 'tell me']) && t.length < 60) return false
  return true
}

export function verdictSummary(j) {
  const pct = Math.round(j.score * 100)
  return `${j.verdict} (${pct}% risk, ${j.category}). ${j.explanation}`
}
