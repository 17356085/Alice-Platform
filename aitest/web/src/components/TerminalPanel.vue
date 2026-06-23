<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import '@xterm/xterm/css/xterm.css'

const props = defineProps<{ wsUrl?: string; autoConnect?: boolean }>()
const container = ref<HTMLElement>()
const connected = ref(false)

let term: Terminal
let fit: FitAddon
let ws: WebSocket | null = null

onMounted(() => {
  term = new Terminal({
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    fontSize: 13,
    theme: {
      background: '#0b0b0f',
      foreground: '#e6e6e6',
      cursor: '#5b7fff',
      selectionBackground: '#1e2040',
      black: '#1a1a1f', red: '#ff5c5c', green: '#4ebe96',
      yellow: '#d2d714', blue: '#818cf8', magenta: '#d946ef',
      cyan: '#479ffa', white: '#e6e6e6',
      brightBlack: '#868f97', brightRed: '#ff8080', brightGreen: '#6ee7b7',
      brightYellow: '#f0f000', brightBlue: '#a5b4fc', brightMagenta: '#e879f9',
      brightCyan: '#67e8f9', brightWhite: '#ffffff',
    },
    cursorBlink: true,
    allowProposedApi: true,
    rows: 20,
  })

  fit = new FitAddon()
  term.loadAddon(fit)
  term.loadAddon(new WebLinksAddon())

  if (container.value) {
    term.open(container.value)
    fit.fit()
  }

  if (props.autoConnect !== false) connect()
  term.writeln('\x1b[1;34m  TLO Terminal — Ready\x1b[0m')
  term.writeln('  Type \x1b[33maitest sop run\x1b[0m to start...\n')
})

onUnmounted(() => {
  ws?.close()
  term?.dispose()
})

function connect() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${location.host}${props.wsUrl || '/ws/kanban'}`)
  ws.onopen = () => { connected.value = true; term.writeln('\x1b[32m  ✅ WebSocket connected\x1b[0m') }
  ws.onclose = () => { connected.value = false; term.writeln('\x1b[31m  ❌ Disconnected — retrying in 3s...\x1b[0m'); setTimeout(connect, 3000) }
  ws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data)
      const ts = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : ''
      switch (msg.type) {
        case 'card_moved':
          term.writeln(`\x1b[36m[${ts}]\x1b[0m \x1b[33m${msg.module}\x1b[0m: ${msg.from_stage} → \x1b[32m${msg.to_stage}\x1b[0m`)
          break
        case 'connected':
          term.writeln(`\x1b[2m[${ts}]\x1b[0m \x1b[2m${msg.connections} client(s) connected\x1b[0m`)
          break
        default:
          term.writeln(`\x1b[2m[${ts}]\x1b[0m ${JSON.stringify(msg).slice(0, 200)}`)
      }
    } catch {
      term.writeln(`\x1b[2m[raw]\x1b[0m ${e.data.slice(0, 300)}`)
    }
  }
}

function clear() { term.clear(); term.writeln('\x1b[1;34m  Cleared\x1b[0m\n') }
</script>

<template>
  <div class="card rounded-lg border border-border overflow-hidden">
    <div class="flex items-center justify-between px-4 py-2 bg-sidebar border-b border-border">
      <div class="flex items-center gap-2 text-xs">
        <span :class="['w-2 h-2 rounded-full', connected ? 'bg-success' : 'bg-destructive']" />
        <span class="text-white font-semibold">Terminal</span>
      </div>
      <div class="flex gap-2">
        <button @click="clear" class="text-xs text-muted-foreground hover:text-white cursor-pointer border-none bg-none font-mono">clear</button>
        <button @click="connect" class="text-xs text-muted-foreground hover:text-white cursor-pointer border-none bg-none font-mono">reconnect</button>
      </div>
    </div>
    <div ref="container" class="h-[360px]" />
  </div>
</template>
