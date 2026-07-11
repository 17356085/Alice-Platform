/** Project Settings — per-project configuration. */
import { useParams } from 'react-router-dom'
import { useSettingsStore } from '@/stores/settings'
import { Settings } from 'lucide-react'

export default function ProjectSettingsView() {
  const { id } = useParams<{ id: string }>()
  const getProjectSettings = useSettingsStore(s => s.getProjectSettings)
  const updateProject = useSettingsStore(s => s.updateProject)
  const ps = getProjectSettings(id || '')

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-xl font-bold mb-6 flex items-center gap-2"><Settings size={20} /> 项目设置</h1>
      <div className="glass-card !rounded-xl p-6 space-y-4">
        <Field label="项目 ID" value={id || ''} />
        <Field label="最大并行数">
          <input type="number" value={ps.maxParallel} onChange={e => updateProject(id || '', { maxParallel: +e.target.value })}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-sm" />
        </Field>
        <Field label="主分支">
          <input value={ps.mainBranch} onChange={e => updateProject(id || '', { mainBranch: e.target.value })}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-sm" />
        </Field>
        <Field label="Provider 覆盖" value={ps.provider || '(全局默认)'} />
        <Field label="Model 覆盖" value={ps.model || '(全局默认)'} />
      </div>
    </div>
  )
}

function Field({ label, value, children }: { label: string; value?: string; children?: React.ReactNode }) {
  return (
    <div>
      <div className="text-[11px] text-muted-foreground mb-1 font-semibold uppercase">{label}</div>
      {children || <div className="text-sm">{value}</div>}
    </div>
  )
}
