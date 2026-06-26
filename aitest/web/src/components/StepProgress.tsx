/** 9-stage step progress indicator — React port. */
interface StepProgressProps {
  current: number   // 0-9
  total?: number    // default 9
  status?: string   // completed / completed_with_issues / in_progress
}

const stages = ['需求', '策略', '设计', '自动化', '环境', '执行', '分析', '报告', '回归']

export default function StepProgress({ current, total = 9, status }: StepProgressProps) {
  return (
    <div className="flex items-center gap-0.5">
      {stages.slice(0, total).map((label, i) => (
        <div key={i} className="relative flex-1 group">
          <div className={`w-3 h-3 rounded-full mx-auto transition-all duration-500 ${
            i < current
              ? (status === 'completed' ? 'bg-success' : status === 'completed_with_issues' ? 'bg-warning' : 'bg-success')
              : i === current
                ? 'bg-primary animate-pulse ring-2 ring-ring/30'
                : 'bg-muted'
          }`} />
          <div className="text-[9px] text-muted-foreground text-center mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {label}
          </div>
          {i < total - 1 && (
            <div className={`absolute top-1.5 left-[60%] w-[80%] h-px -z-10 transition-colors ${
              i < current - 1 ? 'bg-success' : i < current ? 'bg-primary/50' : 'bg-muted'
            }`} />
          )}
        </div>
      ))}
    </div>
  )
}
