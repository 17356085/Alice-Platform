/** Project Settings — per-project configuration. */
import { useParams } from 'react-router-dom'
import { useSettingsStore } from '@/stores/settings'
import { Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { PageHeader } from '@/components/shared'

export default function ProjectSettingsView() {
  const { id } = useParams<{ id: string }>()
  const getProjectSettings = useSettingsStore(s => s.getProjectSettings)
  const updateProject = useSettingsStore(s => s.updateProject)
  const ps = getProjectSettings(id || '')

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6 p-4 sm:p-6">
      <PageHeader eyebrow="Project configuration" title="项目设置" description="只影响当前项目的执行并发与版本控制配置。" actions={<Button variant="outline" size="sm" disabled>保存设置</Button>} />
      <Card>
        <CardHeader><CardTitle className="text-sm">执行与版本控制</CardTitle></CardHeader>
        <CardContent className="flex flex-col gap-5">
        <Field label="项目 ID" value={id || ''} />
        <Field label="最大并行数">
          <Input type="number" min={1} max={32} value={ps.maxParallel} onChange={e => updateProject(id || '', { maxParallel: +e.target.value })} />
        </Field>
        <Field label="主分支">
          <Input value={ps.mainBranch} onChange={e => updateProject(id || '', { mainBranch: e.target.value })} />
        </Field>
        <Field label="Provider 覆盖" value={ps.provider || '(全局默认)'} />
        <Field label="Model 覆盖" value={ps.model || '(全局默认)'} />
        </CardContent>
      </Card>
    </div>
  )
}

function Field({ label, value, children }: { label: string; value?: string; children?: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      {children || <div className="text-sm">{value}</div>}
    </div>
  )
}
