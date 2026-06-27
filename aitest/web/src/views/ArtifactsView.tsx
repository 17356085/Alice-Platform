/** Artifacts — file browser + preview. Character-branded empty state. */
import { FolderOpen } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { useSettingsStore } from '../stores/settings'

const brand: Record<string, { hint: string }> = {
  default:   { hint: 'Run SOP to reveal what shadows hold.' },
  aoko:      { hint: 'Run SOP — results crash in like thunder.' },
  soujuurou: { hint: 'Run SOP to gather what the mountain yields.' },
}

export default function ArtifactsView() {
  const theme = useSettingsStore(s => s.app.theme)
  const b = brand[theme] || brand.default
  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-6 flex items-center gap-2"><FolderOpen size={20} /> 产物</h1>
      <Card className="text-center py-16">
        <CardContent>
          <FolderOpen size={48} className="mx-auto mb-4 opacity-20" />
          <p className="text-xs text-muted-foreground italic">{b.hint}</p>
        </CardContent>
      </Card>
    </div>
  )
}
