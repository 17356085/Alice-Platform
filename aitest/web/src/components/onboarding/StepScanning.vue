<script setup lang="ts">
import { computed } from 'vue'
import { useOnboardingStore } from '@/stores/onboarding'
import { Loader2, Wifi, Globe, Eye } from 'lucide-vue-next'

const store = useOnboardingStore()

const scanningLabel = computed(() => {
  if (store.totalPages > 0) {
    return `Observing pages: ${store.currentPage} (${store.completedPages}/${store.totalPages})`
  }
  if (store.menuTree.length > 0) {
    return 'Menu discovered — expanding to pages...'
  }
  return 'Scanning sidebar menu...'
})
</script>

<template>
  <div class="step-scanning">
    <div class="scan-animation">
      <Globe :size="64" class="globe" />
      <Wifi :size="24" class="wave" />
    </div>

    <h3 class="scan-title">Discovering application structure</h3>
    <p class="scan-subtitle">{{ scanningLabel }}</p>

    <!-- Page progress detail -->
    <div v-if="store.totalPages > 0" class="page-progress">
      <div class="progress-bar">
        <div
          class="progress-fill"
          :style="{ width: (store.totalPages ? (store.completedPages / store.totalPages * 100) : 0) + '%' }"
        />
      </div>
      <div class="page-counter">
        <Loader2 :size="14" class="spin" />
        <span>{{ store.completedPages }} / {{ store.totalPages }} pages</span>
      </div>
    </div>

    <!-- Preview discovered menu (as it comes in) -->
    <div v-if="store.menuTree.length" class="menu-preview">
      <h4>
        <Eye :size="14" />
        Discovered menu ({{ store.menuTree.length }} groups)
      </h4>
      <ul>
        <li v-for="item in store.menuTree.slice(0, 6)" :key="item.label">
          <span class="menu-label">{{ item.label }}</span>
          <span v-if="item.children?.length" class="child-count">
            {{ item.children.length }} pages
          </span>
        </li>
        <li v-if="store.menuTree.length > 6" class="more">
          ...and {{ store.menuTree.length - 6 }} more groups
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.step-scanning {
  text-align: center;
  padding: 32px 0;
}
.scan-animation {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
}
.globe {
  color: var(--primary);
  animation: pulse 2s ease-in-out infinite;
}
.wave {
  position: absolute;
  bottom: 0;
  right: -4px;
  color: var(--success);
  animation: ping 1.5s ease-in-out infinite;
}
.scan-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--foreground);
  margin: 0 0 8px;
}
.scan-subtitle {
  color: var(--muted-foreground);
  font-size: 0.9rem;
  margin: 0;
}

/* Page progress */
.page-progress {
  max-width: 400px;
  margin: 24px auto 0;
}
.progress-bar {
  height: 4px;
  background: var(--secondary);
  border-radius: var(--radius-full);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--primary);
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
}
.page-counter {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 0.85rem;
  color: var(--muted-foreground);
}

/* Menu preview */
.menu-preview {
  max-width: 400px;
  margin: 24px auto 0;
  text-align: left;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
}
.menu-preview h4 {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--muted-foreground);
  margin: 0 0 10px;
}
.menu-preview ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.menu-preview li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.85rem;
}
.menu-preview li:last-child {
  border-bottom: none;
}
.menu-label {
  color: var(--foreground);
  font-weight: 500;
}
.child-count {
  color: var(--muted-foreground);
  font-size: 0.78rem;
}
.more {
  color: var(--muted-foreground);
  font-style: italic;
}

.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(0.95); }
}
@keyframes ping {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
