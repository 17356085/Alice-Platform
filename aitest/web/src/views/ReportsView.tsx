/** Reports — KPI + test reports. */
import { BarChart3, FileText } from 'lucide-react'

export default function ReportsView() {
  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-6 flex items-center gap-2"><BarChart3 size={20} /> 测试报告</h1>
      <div className="grid grid-cols-3 gap-4 mb-6">
        {['通过率', '覆盖率', '缺陷数'].map((label, i) => (
          <div key={i} className="glass-card !rounded-xl p-4 text-center">
            <div className="text-2xl font-bold">—</div>
            <div className="text-[11px] text-muted-foreground mt-1">{label}</div>
          </div>
        ))}
      </div>
      <div className="text-center py-12 text-muted-foreground text-sm">
        <FileText size={48} className="mx-auto mb-4 opacity-20" />
        <p>运行 SOP 后将生成测试报告</p>
      </div>
    </div>
  )
}
