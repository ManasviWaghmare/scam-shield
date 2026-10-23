function Bar({ c, label, value, hint, tone = 'bg-[#2f6bff]' }) {
  const pct = Math.round(Math.min(1, Math.max(0, Number(value) || 0)) * 100)
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs">
        <span className="font-semibold">{label}</span>
        <span className={`font-mono ${c.sub}`}>{pct}%</span>
      </div>
      <div className={`mt-1 h-2 rounded-full overflow-hidden ${c.track}`}
        role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
        <div className={`h-full ${tone} transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
      {hint && <p className={`text-[11px] mt-1 ${c.sub}`}>{hint}</p>}
    </div>
  )
}

export default function FusionBreakdown({ c, result }) {
  if (!result || typeof result.score !== 'number') return null
  const scammy = ['scam', 'suspicious'].includes(result.ml_label)
  const conf = Number(result.ml_confidence ?? 0)
  const mlSignal = scammy ? conf : 0.3 * (1 - conf)
  const ruleRisk = Number(result.rule_risk ?? 0)
  const mlWeighted = 0.6 * mlSignal
  const ruleWeighted = 0.4 * ruleRisk
  const combined = mlWeighted + ruleWeighted
  const floored = result.score > combined + 0.005

  return (
    <section className={`mt-4 rounded-2xl border ${c.line} p-4`}>
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="font-bold text-sm">How this score was built</h3>
        <span className={`text-[10px] font-bold tracking-widest px-2 py-0.5 rounded-full ${c.soft} ${c.sub}`}>
          0.6 · ML + 0.4 · RULES
        </span>
      </div>
      <div className="mt-3">
        <Bar c={c} label={`ML model (${result.ml_label || 'n/a'})`} value={mlSignal}
          hint={`Signal ${(mlSignal * 100).toFixed(0)}% × weight 0.6 = ${mlWeighted.toFixed(2)}`} />
        <Bar c={c} label="Rule & link risk" value={ruleRisk} tone="bg-amber-500"
          hint={`Risk ${(ruleRisk * 100).toFixed(0)}% × weight 0.4 = ${ruleWeighted.toFixed(2)}`} />
        <Bar c={c} label="Final risk score" value={result.score} tone="bg-emerald-500"
          hint={floored
            ? `Rules forced a floor: ${combined.toFixed(2)} → ${result.score.toFixed(2)} (strong explicit signals)`
            : `Fused: ${mlWeighted.toFixed(2)} + ${ruleWeighted.toFixed(2)} = ${combined.toFixed(2)}`} />
      </div>
      <p className={`text-[11px] ${c.sub}`}>
        Verdict badged at 70% (Scam), 40% (Suspicious) — thresholds live in <code>explainer.fuse_verdict()</code>.
      </p>
    </section>
  )
}
