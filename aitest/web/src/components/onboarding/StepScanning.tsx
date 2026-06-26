/** Step: Scanning/progress during onboarding. React port. */
import { useMemo } from 'react'
import { useOnboardingStore } from '@/stores/onboarding'
import { Loader2, Wifi, Globe, Eye } from 'lucide-react'

export default function StepScanning() {
  const totalPages = useOnboardingStore(s => s.totalPages)
  const currentPage = useOnboardingStore(s => s.currentPage)
  const completedPages = useOnboardingStore(s => s.completedPages)
  const menuTree = useOnboardingStore(s => s.menuTree)

  const scanningLabel = useMemo(() => {
    if (totalPages > 0) return `Observing pages: ${currentPage} (${completedPages}/${totalPages})`
    if (menuTree.length > 0) return 'Menu discovered — expanding to pages...'
    return 'Scanning sidebar menu...'
  }, [totalPages, currentPage, completedPages, menuTree])

  return (
    <div className="step-scanning">
      <div className="scan-animation">
        <Globe size={64} className="globe" />
        <Wifi size={24} className="wave" />
      </div>
      <h3 className="scan-title">Discovering application structure</h3>
      <p className="scan-subtitle">{scanningLabel}</p>
      {totalPages > 0 && (
        <div className="page-progress">
          <div className="progress-bar"><div className="progress-fill" style={{ width: totalPages ? (completedPages / totalPages * 100) + '%' : '0%' }} /></div>
          <div className="page-counter"><Loader2 size={14} className="spin" /><span>{completedPages} / {totalPages} pages</span></div>
        </div>
      )}
      {menuTree.length > 0 && (
        <div className="menu-preview">
          <h4><Eye size={14} /> Discovered menu ({menuTree.length} groups)</h4>
          <ul>
            {menuTree.slice(0, 6).map(item => (
              <li key={item.label}><span className="menu-label">{item.label}</span>
                {item.children?.length ? <span className="child-count">{item.children.length} pages</span> : null}
              </li>
            ))}
            {menuTree.length > 6 && <li className="more">...and {menuTree.length - 6} more groups</li>}
          </ul>
        </div>
      )}
      <style>{`
        .step-scanning { text-align: center; padding: 32px 0; }
        .scan-animation { position: relative; width: 80px; height: 80px; margin: 0 auto 24px; }
        .globe { color: var(--primary); animation: pulse 2s ease-in-out infinite; }
        .wave { position: absolute; bottom: 0; right: -4px; color: var(--success); animation: ping 1.5s ease-in-out infinite; }
        .scan-title { font-size: 1.15rem; font-weight: 600; color: var(--foreground); margin: 0 0 8px; }
        .scan-subtitle { color: var(--muted-foreground); font-size: 0.9rem; margin: 0; }
        .page-progress { max-width: 400px; margin: 24px auto 0; }
        .progress-bar { height: 4px; background: var(--secondary); border-radius: var(--radius-full); overflow: hidden; }
        .progress-fill { height: 100%; background: var(--primary); border-radius: var(--radius-full); transition: width 0.3s ease; }
        .page-counter { display: flex; align-items: center; justify-content: center; gap: 6px; margin-top: 8px; font-size: 0.85rem; color: var(--muted-foreground); }
        .menu-preview { max-width: 400px; margin: 24px auto 0; text-align: left; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; }
        .menu-preview h4 { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; color: var(--muted-foreground); margin: 0 0 10px; }
        .menu-preview ul { list-style: none; padding: 0; margin: 0; }
        .menu-preview li { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 0.85rem; }
        .menu-preview li:last-child { border-bottom: none; }
        .menu-label { color: var(--foreground); font-weight: 500; }
        .child-count { color: var(--muted-foreground); font-size: 0.78rem; }
        .more { color: var(--muted-foreground); font-style: italic; }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100% { opacity:1; transform:scale(1) } 50% { opacity:.7; transform:scale(.95) } }
        @keyframes ping { 0%,100% { opacity:1 } 50% { opacity:.4 } }
      `}</style>
    </div>
  )
}
