<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface ToastMsg {
  id: number
  text: string
  type: 'success' | 'error' | 'warning' | 'info'
  ts: number
}

const toasts = ref<ToastMsg[]>([])
let nextId = 0

function addToast(text: string, type: ToastMsg['type'] = 'info', duration = 3000) {
  const id = nextId++
  toasts.value.push({ id, text, type, ts: Date.now() })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, duration)
}

// Expose globally for any component to use
;(window as any).__tlo_toast = { add: addToast }

defineExpose({ add: addToast })
</script>

<template>
  <div class="fixed bottom-5 right-5 z-[100] flex flex-col gap-2 pointer-events-none">
    <div
      v-for="t in toasts"
      :key="t.id"
      :class="[
        'px-4 py-2.5 rounded-lg text-sm font-medium shadow-lg pointer-events-auto transition-all duration-300 animate-slide-up max-w-[360px]',
        t.type === 'success' ? 'bg-success text-success-foreground' :
        t.type === 'error' ? 'bg-destructive text-destructive-foreground' :
        t.type === 'warning' ? 'bg-warning text-warning-foreground' :
        'bg-card text-foreground border border-border'
      ]"
    >
      <span class="mr-2">
        {{ t.type === 'success' ? '✅' : t.type === 'error' ? '❌' : t.type === 'warning' ? '⚠️' : 'ℹ️' }}
      </span>
      {{ t.text }}
    </div>
  </div>
</template>

<style scoped>
@keyframes slide-up {
  from { transform: translateY(16px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.animate-slide-up { animation: slide-up 0.3s ease-out; }
</style>
