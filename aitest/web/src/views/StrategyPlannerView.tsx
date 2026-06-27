/** Strategy Planner — test strategy table. */
import { Lightbulb } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

export default function StrategyPlannerView() {
  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-6 flex items-center gap-2">
        <Lightbulb size={20} /> 策略规划
      </h1>
      <Card className="p-4 mb-4">
        <div className="text-sm font-mono text-muted-foreground">
          Risk_Score = diff(0.4) + defect_heat(0.35) + fail_rate(0.25)
        </div>
      </Card>
      <Card className="text-center py-12">
        <CardContent>
          <p className="text-sm text-muted-foreground">选择模块后查看风险评分和测试建议</p>
        </CardContent>
      </Card>
    </div>
  )
}
