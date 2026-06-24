/**
 * Lightweight memory/DOM diagnostic overlay.
 * Enabled only when URL contains ?debug=1
 *
 * Usage: http://localhost:15173/?debug=1
 */
export function initMemoryDebug() {
  if (!location.search.includes('debug=1')) return

  // ── Create overlay ──
  const el = document.createElement('div')
  el.id = '__tlo_debug'
  Object.assign(el.style, {
    position: 'fixed', bottom: '8px', right: '8px', zIndex: '99999',
    background: 'rgba(0,0,0,0.85)', color: '#0f0', fontFamily: 'monospace',
    fontSize: '11px', padding: '8px 12px', borderRadius: '6px',
    lineHeight: '1.6', maxWidth: '320px', pointerEvents: 'none',
  })
  document.body.appendChild(el)

  // ── Collect stats ──
  function stats() {
    const mem = (performance as any).memory
    const heapMB = mem ? (mem.usedJSHeapSize / 1024 / 1024).toFixed(1) : '?'
    const heapLimitMB = mem ? (mem.jsHeapSizeLimit / 1024 / 1024).toFixed(0) : '?'
    const domNodes = document.querySelectorAll('*').length
    const vueApps = (document.getElementById('app') as any)?._vnode ? 1 : 0

    return [
      `Heap: ${heapMB} / ${heapLimitMB} MB`,
      `DOM:  ${domNodes} nodes`,
      `Vue:  ${vueApps} app(s)`,
      `Time: ${new Date().toLocaleTimeString()}`,
    ].join('\n')
  }

  // ── Update loop ──
  function tick() {
    el.textContent = stats()
    requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}
