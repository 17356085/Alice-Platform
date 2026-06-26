/** Markdown renderer — React port. Vue v-html → React dangerouslySetInnerHTML.
 *  Vue :deep() selectors → descendant CSS classes (no shadow DOM in React).
 */
import { useMemo } from 'react'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

export default function Markdown({ content }: { content: string }) {
  const html = useMemo(() => {
    try {
      return marked.parse(content || '') as string
    } catch {
      return content || ''
    }
  }, [content])

  return (
    <>
      <div
        className="prose prose-sm dark:prose-invert max-w-none"
        dangerouslySetInnerHTML={{ __html: html }}
      />
      <style>{`
        .prose { line-height: 1.7; }
        .prose h1 { font-size: 1.5rem; font-weight: 700; margin-top: 1rem; margin-bottom: 0.5rem; }
        .prose h2 { font-size: 1.2rem; font-weight: 700; margin-top: 1rem; margin-bottom: 0.5rem; }
        .prose h3 { font-size: 1.05rem; font-weight: 600; margin-top: 0.75rem; margin-bottom: 0.4rem; }
        .prose p { margin-bottom: 0.5rem; }
        .prose ul, .prose ol { padding-left: 1.5rem; margin-bottom: 0.5rem; }
        .prose li { margin-bottom: 0.15rem; }
        .prose code { font-family: var(--font-mono); font-size: 0.85em; background: var(--muted); padding: 1px 5px; border-radius: 4px; }
        .prose pre { background: var(--muted); padding: 12px 16px; border-radius: 8px; overflow-x: auto; margin: 0.5rem 0; }
        .prose pre code { background: none; padding: 0; }
        .prose table { width: 100%; border-collapse: collapse; margin: 0.5rem 0; font-size: 0.85rem; }
        .prose th { text-align: left; padding: 6px 10px; background: var(--muted); font-weight: 600; border-bottom: 2px solid var(--border); }
        .prose td { padding: 5px 10px; border-bottom: 1px solid var(--border); }
        .prose strong { font-weight: 700; color: var(--foreground); }
        .prose a { color: var(--primary); text-decoration: underline; }
        .prose blockquote { border-left: 3px solid var(--primary); padding-left: 12px; margin: 0.5rem 0; color: var(--muted-foreground); }
        .prose hr { border: none; border-top: 1px solid var(--border); margin: 1rem 0; }
      `}</style>
    </>
  )
}
