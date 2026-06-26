/** Simple SVG line chart — React port. No dependencies. */
import { useMemo } from 'react'

interface Point { ts: string; total_tokens: number; workflow_rate: number; uptime_s: number }

interface TrendChartProps {
  points: Point[]
  metric: 'total_tokens' | 'workflow_rate'
  width?: number
  height?: number
}

const PAD = { top: 16, right: 16, bottom: 24, left: 48 }

export default function TrendChart({ points, metric, width = 600, height = 160 }: TrendChartProps) {
  const chartW = width - PAD.left - PAD.right
  const chartH = height - PAD.top - PAD.bottom

  const result = useMemo(() => {
    const values = points.map(p => p[metric] || 0)
    const maxVal = Math.max(...values, 1)
    const minVal = Math.min(...values, 0)

    function x(i: number): number {
      if (values.length <= 1) return PAD.left + chartW / 2
      return PAD.left + (i / (values.length - 1)) * chartW
    }
    function y(v: number): number {
      const range = maxVal - minVal || 1
      return PAD.top + chartH - ((v - minVal) / range) * chartH
    }

    const pathD = values.length
      ? values.map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' ')
      : ''

    const areaD = values.length > 1
      ? `${pathD} L ${x(values.length - 1).toFixed(1)} ${y(minVal).toFixed(1)} L ${x(0).toFixed(1)} ${y(minVal).toFixed(1)} Z`
      : ''

    const yTicks = (() => {
      const count = 4
      const ticks: { value: number; y: number; label: string }[] = []
      for (let i = 0; i <= count; i++) {
        const v = minVal + (maxVal - minVal) * (i / count)
        ticks.push({
          value: v, y: y(v),
          label: metric === 'workflow_rate'
            ? Math.round(v * 100) + '%'
            : v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v.toFixed(0),
        })
      }
      return ticks
    })()

    return { values, pathD, areaD, yTicks, x, y }
  }, [points, metric, chartW, chartH])

  const label = metric === 'workflow_rate' ? 'Success Rate' : 'Tokens'

  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} className="chart-svg">
        {/* Grid lines */}
        {result.yTicks.map(t => (
          <line key={`g${t.value}`}
            x1={PAD.left} x2={width - PAD.right} y1={t.y} y2={t.y}
            stroke="#e5e7eb" strokeWidth={0.5} strokeDasharray="3 3"
          />
        ))}
        {/* Y labels */}
        {result.yTicks.map(t => (
          <text key={`yl${t.value}`}
            x={PAD.left - 6} y={t.y + 4}
            textAnchor="end" fontSize={10} fill="#9ca3af"
          >{t.label}</text>
        ))}

        {/* Area fill */}
        {result.values.length > 1 && (
          <path d={result.areaD} fill="url(#grad)" opacity={0.15} />
        )}
        <defs>
          <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>

        {/* Line */}
        {result.values.length > 1 && (
          <path d={result.pathD} fill="none" stroke="#3b82f6" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        )}

        {/* Dots */}
        {result.values.map((v, i) => (
          <circle key={`d${i}`}
            cx={result.x(i)} cy={result.y(v)} r={3}
            fill="white" stroke="#3b82f6" strokeWidth={1.5}
          />
        ))}

        {/* X labels */}
        {points.length > 0 && (
          <text x={result.x(0)} y={height - 4} textAnchor="start" fontSize={9} fill="#9ca3af">
            {points[0].ts?.slice(5, 16) || ''}
          </text>
        )}
        {points.length > 1 && (
          <text x={result.x(points.length - 1)} y={height - 4} textAnchor="end" fontSize={9} fill="#9ca3af">
            {points[points.length - 1].ts?.slice(5, 16) || ''}
          </text>
        )}
      </svg>
      <div className="chart-label">{label}</div>
      <style>{`
        .chart-wrap { width: 100%; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 10px; padding: 8px 0 0; }
        .chart-svg { width: 100%; height: auto; display: block; }
        .chart-label { text-align: center; font-size: 11px; color: var(--text-muted); padding: 4px 0 8px; }
      `}</style>
    </div>
  )
}
