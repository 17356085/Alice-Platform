/** Step: Review and confirm discovered menu structure. React port. */
import { useState, useMemo } from 'react'
import { useOnboardingStore, type MenuNode } from '@/stores/onboarding'
import { Check, Pencil, X } from 'lucide-react'

export default function StepConfirmMenu() {
  const menuTree = useOnboardingStore(s => s.menuTree)
  const confirmMenu = useOnboardingStore(s => s.confirmMenu)
  const step = useOnboardingStore(s => s.step)
  const [editingLabel, setEditingLabel] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')

  function startEdit(label: string) { setEditingLabel(label); setEditValue(label) }
  function saveEdit() {
    if (!editingLabel || !editValue.trim()) return
    const oldLabel = editingLabel, newLabel = editValue.trim()
    function rename(items: MenuNode[]) {
      for (const item of items) {
        if (item.label === oldLabel) item.label = newLabel
        if (item.children) rename(item.children)
      }
    }
    const tree = [...menuTree]
    rename(tree)
    useOnboardingStore.setState({ menuTree: tree })
    setEditingLabel(null); setEditValue('')
  }

  async function handleConfirm() { await confirmMenu(menuTree) }

  return (
    <div className="step-confirm">
      <h3>Review discovered menu structure</h3>
      <p className="subtitle">
        TLO discovered {menuTree.length} menu groups from the sidebar.
        Edit labels or remove items before continuing.
      </p>
      {!menuTree.length ? (
        <div className="empty"><p>No menu items discovered yet. Waiting for scan to complete...</p></div>
      ) : (
        <div className="menu-tree">
          {menuTree.map(group => (
            <div key={group.label} className="menu-group">
              <div className="group-header">
                <span className="group-label">{group.label}</span>
                {group.children?.length ? <span className="badge">{group.children.length} pages</span> : null}
              </div>
              {group.children?.length ? (
                <ul className="page-list">
                  {group.children.map(page => (
                    <li key={page.label} className="page-item">
                      {editingLabel === page.label ? (
                        <>
                          <input value={editValue} onChange={e => setEditValue(e.target.value)} className="edit-input" onKeyUp={e => { e.key === 'Enter' && saveEdit(); e.key === 'Escape' && setEditingLabel(null) }} autoFocus />
                          <button className="btn-icon save" onClick={saveEdit}><Check size={14} /></button>
                          <button className="btn-icon cancel" onClick={() => setEditingLabel(null)}><X size={14} /></button>
                        </>
                      ) : (
                        <>
                          <span className="page-label">{page.label}</span>
                          <code className="page-route">{page.route}</code>
                          <button className="btn-icon edit" onClick={() => startEdit(page.label)}><Pencil size={13} /></button>
                        </>
                      )}
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ))}
        </div>
      )}
      <div className="actions">
        <p className="note">You can edit labels above. Click "Continue" to proceed with page discovery.</p>
        <button className="btn-confirm" disabled={step !== 'confirm_menu'} onClick={handleConfirm}>
          <Check size={16} /> Continue with {menuTree.length} groups
        </button>
      </div>
      <style>{`
        .step-confirm { padding: 16px 0; }
        .step-confirm h3 { font-size: 1.1rem; font-weight: 600; margin: 0 0 6px; }
        .subtitle { color: var(--muted-foreground); font-size: 0.85rem; margin: 0 0 20px; }
        .empty { text-align: center; color: var(--muted-foreground); padding: 32px; }
        .menu-tree { display: flex; flex-direction: column; gap: 12px; max-height: 420px; overflow-y: auto; }
        .menu-group { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 12px 16px; }
        .group-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
        .group-label { font-weight: 600; font-size: 0.9rem; color: var(--foreground); }
        .badge { background: var(--primary); color: var(--primary-foreground); font-size: 0.7rem; padding: 1px 8px; border-radius: var(--radius-full); }
        .page-list { list-style: none; padding: 0; margin: 0; }
        .page-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: var(--radius-sm); transition: background 0.1s; }
        .page-item:hover { background: var(--secondary); }
        .page-label { font-size: 0.85rem; color: var(--foreground); flex: 1; }
        .page-route { font-size: 0.75rem; color: var(--muted-foreground); background: var(--secondary); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono); }
        .edit-input { flex: 1; padding: 4px 8px; border: 1px solid var(--primary); border-radius: var(--radius-sm); font-size: 0.85rem; }
        .btn-icon { background: none; border: none; cursor: pointer; padding: 2px; border-radius: 4px; color: var(--muted-foreground); }
        .btn-icon:hover { background: var(--secondary); }
        .btn-icon.save { color: var(--success); }
        .btn-icon.cancel { color: var(--destructive); }
        .actions { margin-top: 24px; text-align: center; }
        .note { color: var(--muted-foreground); font-size: 0.8rem; margin: 0 0 12px; }
        .btn-confirm { display: inline-flex; align-items: center; gap: 8px; padding: 10px 28px; background: var(--success); color: var(--success-foreground); border: none; border-radius: var(--radius-md); font-size: 0.9rem; font-weight: 600; cursor: pointer; }
        .btn-confirm:hover:not(:disabled) { filter: brightness(1.1); }
        .btn-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
      `}</style>
    </div>
  )
}
