<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'

// Configure marked for safe rendering
marked.setOptions({ breaks: true, gfm: true })

const props = defineProps<{ content: string }>()
const html = computed(() => marked.parse(props.content || '') as string)
</script>

<template>
  <div class="prose prose-sm dark:prose-invert max-w-none" v-html="html" />
</template>

<style scoped>
/* Markdown prose styling — :deep() penetrates v-html rendered content */
.prose { line-height: 1.7; }
.prose :deep(h1) { font-size: 1.5rem; font-weight: 700; margin-top: 1rem; margin-bottom: 0.5rem; }
.prose :deep(h2) { font-size: 1.2rem; font-weight: 700; margin-top: 1rem; margin-bottom: 0.5rem; }
.prose :deep(h3) { font-size: 1.05rem; font-weight: 600; margin-top: 0.75rem; margin-bottom: 0.4rem; }
.prose :deep(p) { margin-bottom: 0.5rem; }
.prose :deep(ul), .prose :deep(ol) { padding-left: 1.5rem; margin-bottom: 0.5rem; }
.prose :deep(li) { margin-bottom: 0.15rem; }
.prose :deep(code) { font-family: var(--font-mono); font-size: 0.85em; background: var(--muted); padding: 1px 5px; border-radius: 4px; }
.prose :deep(pre) { background: var(--muted); padding: 12px 16px; border-radius: 8px; overflow-x: auto; margin: 0.5rem 0; }
.prose :deep(pre code) { background: none; padding: 0; }
.prose :deep(table) { width: 100%; border-collapse: collapse; margin: 0.5rem 0; font-size: 0.85rem; }
.prose :deep(th) { text-align: left; padding: 6px 10px; background: var(--muted); font-weight: 600; border-bottom: 2px solid var(--border); }
.prose :deep(td) { padding: 5px 10px; border-bottom: 1px solid var(--border); }
.prose :deep(strong) { font-weight: 700; color: var(--foreground); }
.prose :deep(a) { color: var(--primary); text-decoration: underline; }
.prose :deep(blockquote) { border-left: 3px solid var(--primary); padding-left: 12px; margin: 0.5rem 0; color: var(--muted-foreground); }
.prose :deep(hr) { border: none; border-top: 1px solid var(--border); margin: 1rem 0; }
</style>
