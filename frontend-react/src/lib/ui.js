export function cls(dark) {
  return {
    dark,
    page: dark ? 'min-h-screen bg-[#04070f] text-zinc-100' : 'min-h-screen bg-stone-100 text-stone-900',
    panel: dark ? 'card' : 'bg-white border border-stone-200 rounded-[20px] shadow-sm',
    sub: dark ? 'text-zinc-400' : 'text-stone-500',
    input: dark
      ? 'mt-4 w-full border border-white/10 rounded-2xl p-4 text-sm bg-[#070d1d] focus:outline-none focus:ring-2 focus:ring-[#2f6bff]'
      : 'mt-4 w-full border border-stone-200 rounded-2xl p-4 text-sm bg-stone-50 focus:outline-none focus:ring-2 focus:ring-emerald-600',
    chip: dark
      ? 'text-xs border border-white/10 rounded-full px-3 py-1.5 hover:border-[#2f6bff]'
      : 'text-xs border border-stone-200 rounded-full px-3 py-1.5 hover:border-emerald-600',
    line: dark ? 'border-white/10' : 'border-stone-200',
    tabOff: dark ? 'border border-white/10' : 'border border-stone-200',
    tabOn: dark ? 'bg-zinc-100 text-zinc-900' : 'bg-stone-900 text-white',
    soft: dark ? 'bg-white/5' : 'bg-stone-100',
    track: dark ? 'bg-white/10' : 'bg-stone-200',
  }
}
