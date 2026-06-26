/** Knowledge Base — ChromaDB + memory hits. */
import { BookOpen, Database } from 'lucide-react'

export default function KnowledgeView() {
  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-6 flex items-center gap-2"><BookOpen size={20} /> 知识库</h1>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="glass-card !rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-info">—</div>
          <div className="text-[11px] text-muted-foreground mt-1">集合</div>
        </div>
        <div className="glass-card !rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-success">—</div>
          <div className="text-[11px] text-muted-foreground mt-1">文档</div>
        </div>
        <div className="glass-card !rounded-xl p-4 text-center">
          <span className="w-2 h-2 rounded-full bg-success inline-block mr-1" />
          <span className="text-[11px] text-muted-foreground">ChromaDB</span>
        </div>
      </div>
      <div className="text-center py-12 text-muted-foreground text-sm">
        <Database size={48} className="mx-auto mb-4 opacity-20" />
        <p>运行 SOP 后将填充知识库数据</p>
      </div>
    </div>
  )
}
