<script setup lang="ts">
import { computed } from 'vue'
import { useOnboardingStore } from '@/stores/onboarding'
import { useProjectStore } from '@/stores/project'
import { CheckCircle2, FolderOpen, FileText, Layers, ArrowRight } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const store = useOnboardingStore()
const projectStore = useProjectStore()
const router = useRouter()

// Group pages by menu group
const pagesByGroup = computed(() => {
  const groups: Record<string, any[]> = {}
  for (const p of store.pages) {
    const key = p.menu_path?.[0] || 'Other'
    if (!groups[key]) groups[key] = []
    groups[key].push(p)
  }
  return groups
})

const groupCount = computed(() => Object.keys(pagesByGroup.value).length)

function openProject() {
  // Register project + set active → sidebar shows workspace
  if (store.projectId) {
    projectStore.addProject({
      id: store.projectId,
      name: store.projectId,
      path: store.projectPath || store.baseUrl,
      modules: Object.keys(pagesByGroup.value),
      status: 'discovered',
    })
    projectStore.setActive(store.projectId)
  }
  router.push({ path: '/kanban', query: { project: store.projectId } })
}
</script>

<template>
  <div class="step-results">
    <div class="success-icon">
      <CheckCircle2 :size="56" />
    </div>

    <h3>Project Ready!</h3>
    <p class="summary">
      <strong>{{ store.projectId }}</strong> has been onboarded successfully.
    </p>

    <div class="stats-grid">
      <div class="stat">
        <Layers :size="20" />
        <div>
          <span class="stat-value">{{ groupCount }}</span>
          <span class="stat-label">Menu Groups</span>
        </div>
      </div>
      <div class="stat">
        <FileText :size="20" />
        <div>
          <span class="stat-value">{{ store.pages.length }}</span>
          <span class="stat-label">Pages Discovered</span>
        </div>
      </div>
      <div class="stat">
        <FolderOpen :size="20" />
        <div>
          <span class="stat-value">{{ Object.keys(pagesByGroup).length }}</span>
          <span class="stat-label">Modules Created</span>
        </div>
      </div>
    </div>

    <!-- Page breakdown -->
    <div v-if="Object.keys(pagesByGroup).length" class="breakdown">
      <h4>Page Breakdown</h4>
      <div v-for="(pages, group) in pagesByGroup" :key="group" class="group-section">
        <h5>{{ group }} <span class="count">{{ pages.length }} pages</span></h5>
        <ul>
          <li v-for="p in pages" :key="p.id">
            <code>{{ p.route }}</code>
            <span>{{ p.title }}</span>
          </li>
        </ul>
      </div>
    </div>

    <div class="actions">
      <button class="btn-open" @click="openProject">
        <ArrowRight :size="16" />
        Open Project Kanban
      </button>
    </div>
  </div>
</template>

<style scoped>
.step-results {
  text-align: center;
  padding: 16px 0;
}
.success-icon {
  color: var(--success);
  margin-bottom: 16px;
}
h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--foreground);
  margin: 0 0 6px;
}
.summary {
  color: var(--muted-foreground);
  font-size: 0.9rem;
  margin: 0 0 24px;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}
.stat {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--primary);
}
.stat-value {
  display: block;
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--foreground);
}
.stat-label {
  display: block;
  font-size: 0.75rem;
  color: var(--muted-foreground);
}

/* Breakdown */
.breakdown {
  text-align: left;
  margin-bottom: 24px;
}
.breakdown h4 {
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0 0 12px;
}
.group-section {
  margin-bottom: 12px;
}
.group-section h5 {
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0 0 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.count {
  font-weight: 400;
  color: var(--muted-foreground);
  font-size: 0.78rem;
}
.group-section ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.group-section li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 8px;
  font-size: 0.82rem;
  border-radius: var(--radius-sm);
}
.group-section li:hover {
  background: var(--secondary);
}
.group-section code {
  font-size: 0.75rem;
  color: var(--muted-foreground);
  background: var(--secondary);
  padding: 1px 6px;
  border-radius: 3px;
  min-width: 120px;
  font-family: var(--font-mono);
}

/* Actions */
.actions {
  margin-top: 8px;
}
.btn-open {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 32px;
  background: var(--primary);
  color: var(--primary-foreground);
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
}
.btn-open:hover { filter: brightness(1.1); }
</style>
