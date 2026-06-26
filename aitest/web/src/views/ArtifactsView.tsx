/** Artifacts — file browser + preview. */
import { FolderOpen } from 'lucide-react'

export default function ArtifactsView() {
  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-6 flex items-center gap-2"><FolderOpen size={20} /> 产物</h1>
      <div className="text-center py-16 text-muted-foreground text-sm">
        <FolderOpen size={48} className="mx-auto mb-4 opacity-20" />
        <p>测试产物浏览器</p>
        <span className="text-xs">运行 SOP 后此处将显示生成的测试文件、报告和日志</span>
      </div>
    </div>
  )
}
