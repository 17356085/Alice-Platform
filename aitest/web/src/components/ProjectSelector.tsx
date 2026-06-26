/** Project selector dropdown — React port.
 *  Vue RouterLink → React Router Link.
 */
import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useProjectStore, type ProjectInfo } from '../stores/project'
import { ChevronDown, Plus, FolderOpen } from 'lucide-react'

export default function ProjectSelector() {
  const projects = useProjectStore(s => s.projects)
  const activeId = useProjectStore(s => s.activeId)
  const activeProject = useProjectStore(s => s.activeProject())
  const setActive = useProjectStore(s => s.setActive)

  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')

  const select = (p: ProjectInfo) => {
    setActive(p.id)
    setOpen(false)
  }

  const filtered = useMemo(() => {
    if (!search) return projects
    const q = search.toLowerCase()
    return projects.filter(p => (p.name || p.id).toLowerCase().includes(q))
  }, [projects, search])

  return (
    <div className="project-selector">
      <button className="selector-trigger" onClick={() => setOpen(!open)}>
        <FolderOpen size={16} />
        <span className="project-name">
          {activeProject?.name || activeProject?.id || '选择项目'}
        </span>
        <ChevronDown size={14} className={open ? 'rotated' : ''} />
      </button>

      {/* Backdrop */}
      {open && <div className="backdrop" onClick={() => setOpen(false)} />}

      {open && (
        <div className="selector-dropdown">
          <input
            className="search-input"
            placeholder="搜索项目..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <div className="project-list">
            {filtered.map(p => (
              <button
                key={p.id}
                className={`project-item${p.id === activeId ? ' active' : ''}`}
                onClick={() => select(p)}
              >
                <div className="item-info">
                  <span className="item-name">{p.name || p.id}</span>
                  <span className="item-meta">{p.modules?.length || 0} 模块</span>
                </div>
                {p.status && (
                  <span className={`item-status ${p.status}`}>{p.status}</span>
                )}
              </button>
            ))}
            {!filtered.length && <div className="empty">No projects found</div>}
          </div>
          <div className="dropdown-footer">
            <Link to="/onboarding" className="new-project-btn" onClick={() => setOpen(false)}>
              <Plus size={14} /> 新建项目
            </Link>
          </div>
        </div>
      )}

      <style>{`
        .project-selector { position: relative; }
        .selector-trigger {
          display: flex; align-items: center; gap: 6px;
          padding: 6px 12px; border-radius: 8px;
          background: var(--bg-secondary); border: 1px solid var(--border);
          cursor: pointer; font-size: 13px; color: var(--text-primary);
        }
        .selector-trigger:hover { background: var(--bg-hover); }
        .project-name { max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .rotated { transform: rotate(180deg); transition: transform .2s; }
        .backdrop { position: fixed; inset: 0; z-index: 99; }
        .selector-dropdown {
          position: absolute; top: 100%; left: 0; margin-top: 4px;
          width: 280px; max-height: 360px;
          background: var(--bg-primary); border: 1px solid var(--border);
          border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,.15);
          z-index: 100; overflow: hidden;
        }
        .search-input {
          width: 100%; padding: 10px 12px; border: none; border-bottom: 1px solid var(--border);
          background: transparent; color: var(--text-primary); outline: none; font-size: 13px;
        }
        .project-list { max-height: 260px; overflow-y: auto; }
        .project-item {
          display: flex; align-items: center; justify-content: space-between;
          width: 100%; padding: 10px 12px; border: none; background: transparent;
          cursor: pointer; font-size: 13px; color: var(--text-primary);
        }
        .project-item:hover, .project-item.active { background: var(--bg-secondary); }
        .item-info { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; }
        .item-name { font-weight: 500; }
        .item-meta { font-size: 11px; color: var(--text-muted); }
        .item-status { font-size: 10px; padding: 2px 6px; border-radius: 4px; }
        .item-status.completed { background: #d4edda; color: #155724; }
        .empty { padding: 20px; text-align: center; color: var(--text-muted); font-size: 13px; }
        .dropdown-footer { border-top: 1px solid var(--border); padding: 6px; }
        .new-project-btn {
          display: flex; align-items: center; gap: 4px; justify-content: center;
          width: 100%; padding: 8px; border-radius: 6px; border: 1px dashed var(--border);
          background: transparent; cursor: pointer; font-size: 12px; color: var(--text-secondary);
          text-decoration: none;
        }
        .new-project-btn:hover { background: var(--bg-secondary); }
      `}</style>
    </div>
  )
}
