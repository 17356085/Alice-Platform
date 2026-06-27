/** Knowledge Base — ChromaDB + memory hits. Character-branded. */
import { BookOpen, Database } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { useSettingsStore } from '../stores/settings'

const brand: Record<string, { hint: string }> = {
  default:   { hint: 'Knowledge blooms in moonlight.' },
  aoko:      { hint: 'Knowledge hits like a bullet.' },
  soujuurou: { hint: 'Knowledge grows steady, like trees.' },
}

export default function KnowledgeView() {
  const theme = useSettingsStore(s => s.app.theme)
  const b = brand[theme] || brand.default
  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-6 flex items-center gap-2"><BookOpen size={20} /> 知识库</h1>
      <div className="grid grid-cols-3 gap-4 mb-6">
        {['集合', '文档', 'ChromaDB'].map((label, i) => (
          <Card key={i} className="p-4 text-center">
            <div className="text-2xl font-bold text-muted-foreground">—</div>
            <div className="text-[11px] text-muted-foreground mt-1">{label}</div>
          </Card>
        ))}
      </div>
      <Card className="text-center py-12">
        <CardContent>
          <Database size={48} className="mx-auto mb-4 opacity-20" />
          <p className="text-xs text-muted-foreground italic">{b.hint}</p>
        </CardContent>
      </Card>
    </div>
  )
}
