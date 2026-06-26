/** AI tool usage indicator — React port.
 *  No Vue dependency — pure presentational component.
 */
interface ToolIndicatorProps {
  tool: string
  input: string
}

const toolMeta: Record<string, { icon: string; color: string; label: string }> = {
  Read: { icon: '📄', color: 'text-blue-400', label: 'Reading file' },
  Glob: { icon: '📁', color: 'text-amber-400', label: 'Searching files' },
  Grep: { icon: '🔎', color: 'text-green-400', label: 'Searching code' },
}

export default function ToolIndicator({ tool, input }: ToolIndicatorProps) {
  if (!tool) return null
  const meta = toolMeta[tool] || { icon: '🔧', color: 'text-muted-foreground', label: tool }

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 text-xs animate-pulse">
      <span className={meta.color}>{meta.icon}</span>
      <span className="text-muted-foreground">{meta.label}</span>
      <span className="text-muted-foreground/50 font-mono truncate max-w-[200px]">{input}</span>
    </div>
  )
}
