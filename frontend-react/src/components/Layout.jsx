const LINKS = [
  ['#/', 'Home'],
  ['#/dashboard', 'Dashboard'],
  ['#/learn', 'Learn'],
  ['#/chat', 'Assistant'],
  ['#/about', 'About'],
]

export default function Layout({ c, route, theme, setTheme, children }) {
  return (
    <div className={c.page}>
      <header className={`sticky top-0 z-40 backdrop-blur border-b ${c.dark ? 'bg-[#04070f]/85 border-white/10' : 'bg-white/85 border-stone-200'}`}>
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between gap-3">
          <a href="#/" className="flex items-center gap-2.5">
            <span className="w-7 h-7 rounded-lg bg-[#2f6bff] text-white flex items-center justify-center font-bold text-sm" style={{ boxShadow: '0 0 18px rgba(47,107,255,.6)' }}>S</span>
            <span className="font-bold tracking-widest text-sm">SCAM SHIELD</span>
          </a>
          <nav className="hidden md:flex items-center gap-6 text-sm opacity-80">
            {LINKS.map(([href, label]) => (
              <a key={href} href={href}
                className={route === href ? 'text-[#2f6bff] font-semibold opacity-100' : 'hover:opacity-100'}>
                {label}
              </a>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className={`text-xs border rounded-full px-3.5 py-1.5 ${c.line}`}>
              {c.dark ? 'Light' : 'Dark'}
            </button>
            <a href="tel:1930" className="btn-primary text-xs px-4 py-2">1930</a>
          </div>
        </div>
        <nav className="md:hidden flex gap-4 px-4 pb-2 text-sm overflow-x-auto opacity-90">
          {LINKS.map(([href, label]) => (
            <a key={href} href={href} className={route === href ? 'text-[#2f6bff] font-semibold' : ''}>{label}</a>
          ))}
        </nav>
      </header>
      <main className="max-w-6xl mx-auto px-4 pb-16">{children}</main>
      <footer className={`border-t ${c.line}`}>
        <div className="max-w-6xl mx-auto px-4 py-5 text-xs flex flex-wrap gap-2 justify-between opacity-70">
          <span>SCAM SHIELD · Hack-A-Throne 2026 · AI Guardian for your messages</span>
          <span>Hashes only · raw messages deleted in 24 hours · Helpline 1930</span>
        </div>
      </footer>
    </div>
  )
}
