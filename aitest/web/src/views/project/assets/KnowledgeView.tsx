/** Knowledge Base — ChromaDB + memory hits. Character-branded. */
import { BookOpen, Database } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { useSettingsStore } from '@/stores/settings'
import { PageHeader, EmptyState } from '@/components/shared'

const brand: Record<string, { hint: string }> = {
  default:   { hint: 'Knowledge blooms in moonlight.' },
  aoko:      { hint: 'Knowledge hits like a bullet.' },
  soujuurou: { hint: 'Knowledge grows steady, like trees.' },
}

export default function KnowledgeView() {
  const theme = useSettingsStore(s => s.app.theme)
  const b = brand[theme] || brand.default
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 p-4 sm:p-6">
      <PageHeader title="知识库" description="浏览 Agent 从运行记录、页面结构和失败样本中积累的可复用知识。" />
      <div className="grid gap-3 sm:grid-cols-3">
        {['集合', '文档', 'ChromaDB'].map((label, i) => (
          <Card key={i}><CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-muted-foreground">—</div>
            <div className="text-[11px] text-muted-foreground mt-1">{label}</div>
          </CardContent></Card>
        ))}
      </div>
      <EmptyState icon={Database} title="知识数据尚未加载" description={b.hint} />
    </div>
  )
}
