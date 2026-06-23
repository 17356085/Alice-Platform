<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatSidebar from '@/components/ChatSidebar.vue'
import ToolIndicator from '@/components/ToolIndicator.vue'

const store = useChatStore()
const input = ref('')
const chatEl = ref<HTMLElement>()
const showSidebar = ref(true)

const suggestions = [
  { icon: '📊', label: '测试覆盖', q: '哪些模块测试覆盖最薄弱？' },
  { icon: '🐛', label: 'Bug 趋势', q: '最近有哪些 flaky test？' },
  { icon: '🛡', label: '安全分析', q: '安全测试覆盖如何？' },
  { icon: '📋', label: '模块状态', q: '哪些模块需要补充测试？' },
]

async function send() {
  const text = input.value.trim()
  if (!text || store.streaming) return
  input.value = ''
  await store.sendMessage(text)
  nextTick(() => chatEl.value?.scrollTo({ top: chatEl.value.scrollHeight, behavior: 'smooth' }))
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
}

function selSuggestion(q: string) { input.value = q; send() }
</script>

<template>
  <div class="flex h-[calc(100vh-100px)] -m-5">
    <!-- Sidebar toggle -->
    <button @click="showSidebar = !showSidebar" class="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-6 h-12 bg-card border border-border rounded-r-md flex items-center justify-center cursor-pointer text-muted-foreground hover:text-foreground transition-colors">
      {{ showSidebar ? '◀' : '▶' }}
    </button>

    <ChatSidebar v-if="showSidebar" />

    <div class="flex-1 flex flex-col">
      <!-- Messages -->
      <div ref="chatEl" class="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        <!-- Empty state -->
        <div v-if="store.messages.length === 0 && !store.streaming" class="flex flex-col items-center justify-center h-full text-center space-y-4">
          <div class="text-4xl">💬</div>
          <div class="text-lg font-semibold">Test Intelligence Chat</div>
          <div class="text-xs text-muted-foreground max-w-sm">Ask questions about your test suite. AI can search TEST_CASES.md, trace logs, and RAG knowledge base.</div>
          <div class="grid grid-cols-2 gap-2 mt-4">
            <button v-for="s in suggestions" :key="s.label" @click="selSuggestion(s.q)"
              class="flex items-center gap-2 px-3 py-2 text-xs border border-border rounded-lg hover:border-ring hover:bg-accent/50 cursor-pointer font-sans transition-colors">
              <span>{{ s.icon }}</span> {{ s.label }}
            </button>
          </div>
        </div>

        <!-- Messages -->
        <div v-for="m in store.messages" :key="m.id" class="space-y-1">
          <!-- User -->
          <div v-if="m.role === 'user'" class="flex justify-end">
            <div class="bg-primary/10 text-foreground rounded-2xl rounded-br-md px-4 py-2.5 max-w-[75%] text-sm">
              {{ m.content }}
            </div>
          </div>
          <!-- Assistant -->
          <div v-else class="space-y-2">
            <!-- Tool usage -->
            <div v-if="m.tools?.length" class="ml-2 space-y-0.5">
              <div v-for="t in m.tools" :key="t.input" class="flex items-center gap-2 text-[11px] text-muted-foreground/60">
                <span>{{ t.name === 'Read' ? '📄' : t.name === 'Grep' ? '🔎' : '📁' }}</span>
                <span class="truncate">{{ t.input }}</span>
              </div>
            </div>
            <div class="flex justify-start">
              <div class="bg-card border border-border rounded-2xl rounded-bl-md px-4 py-2.5 max-w-[85%] text-sm prose prose-sm dark:prose-invert" v-html="m.content.replace(/\n/g,'<br>').replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').replace(/\|(.*)\|/g, (match: string) => `<span class='font-mono text-xs'>${match}</span>`).replace(/^- (.*)/gm,'• $1').replace(/^## (.*)/gm,'<h3 class=\'text-base font-semibold mt-3 mb-1\'>$1</h3>')" />
            </div>
            <!-- Suggested tasks -->
            <div v-if="m.suggestedTasks?.length" class="ml-2 space-y-1.5">
              <div v-for="(t, i) in m.suggestedTasks" :key="i" class="bg-card border border-primary/30 rounded-lg p-3 max-w-[350px]">
                <div class="text-[13px] font-semibold">{{ t.title }}</div>
                <div class="text-[11px] text-muted-foreground mt-0.5">{{ t.description }}</div>
                <div class="flex gap-1.5 mt-2">
                  <span v-if="t.category" class="badge badge-info text-[10px]">{{ t.category }}</span>
                  <span v-if="t.complexity" class="text-[10px] text-muted-foreground">{{ t.complexity }}</span>
                  <button class="ml-auto px-2.5 py-0.5 text-[11px] bg-primary text-primary-foreground rounded border-none cursor-pointer font-sans">Create Task</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Streaming -->
        <div v-if="store.streaming" class="space-y-2">
          <ToolIndicator v-if="store.currentTool" :tool="store.currentTool.split(':')[0]" :input="store.currentTool" />
          <div class="bg-card border border-border rounded-2xl rounded-bl-md px-4 py-2.5 max-w-[85%] text-sm">
            {{ store.streamContent }}<span class="animate-pulse">▊</span>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="border-t border-border p-3">
        <div class="flex gap-2">
          <textarea
            v-model="input"
            @keydown="onKeydown"
            :disabled="store.streaming"
            placeholder="Ask about your test suite..."
            rows="2"
            class="flex-1 resize-none px-3 py-2 border border-border rounded-lg bg-background text-sm font-sans focus:border-ring outline-none disabled:opacity-50"
          />
          <button @click="send" :disabled="store.streaming || !input.trim()"
            class="px-4 py-2 bg-primary text-primary-foreground rounded-lg border-none cursor-pointer font-sans text-sm hover:opacity-90 disabled:opacity-50 transition-opacity">
            ↑
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.badge { display:inline-block; padding:1px 6px; border-radius:9999px; font-weight:600; }
.badge-info { background:var(--info-light); color:var(--info); }
</style>
