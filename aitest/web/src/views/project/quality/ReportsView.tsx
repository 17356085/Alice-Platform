/** Reports — KPI + test reports. */
import { BarChart3, FileText } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { PageHeader, EmptyState } from '@/components/shared'

export default function ReportsView() {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 p-4 sm:p-6">
      <PageHeader title="测试报告" description="汇总运行结果、覆盖情况和缺陷趋势，帮助团队决定下一轮 Agent 改进。" />
      <div className="grid gap-3 sm:grid-cols-3">
        {['通过率', '覆盖率', '缺陷数'].map((label, i) => (
          <Card key={i}><CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">—</div>
            <div className="text-[11px] text-muted-foreground mt-1">{label}</div>
          </CardContent></Card>
        ))}
      </div>
      <EmptyState icon={FileText} title="还没有测试报告" description="运行 SOP 后，系统会在这里生成报告与质量趋势。" />
    </div>
  )
}
