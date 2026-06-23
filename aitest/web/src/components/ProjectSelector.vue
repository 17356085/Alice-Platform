<script setup lang="ts">
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useProjectStore, type ProjectInfo } from '../stores/project'
import { ChevronDown, Plus, FolderOpen } from 'lucide-vue-next'

const store = useProjectStore()
const open = ref(false)
const search = ref('')

function select(p: ProjectInfo) {
  store.setActive(p.id)
  open.value = false
}
function toggle() { open.value = !open.value }
function close() { open.value = false }

const filtered = computed(() => {
  if (!search.value) return store.projects
  const q = search.value.toLowerCase()
  return store.projects.filter(p =>
    (p.name || p.id).toLowerCase().includes(q)
  )
})
</script>

<template>
  <div class="project-selector">
    <button class="selector-trigger" @click="toggle">
      <FolderOpen :size="16" />
      <span class="project-name">{{ store.activeProject?.name || store.activeProject?.id || '选择项目' }}</span>
      <ChevronDown :size="14" :class="{ rotated: open }" />
    </button>

    <!-- Backdrop -->
    <div v-if="open" class="backdrop" @click="close" />

    <div v-if="open" class="selector-dropdown">
      <input v-model="search" class="search-input" placeholder="搜索项目..." />
      <div class="project-list">
        <button
          v-for="p in filtered"
          :key="p.id"
          class="project-item"
          :class="{ active: p.id === store.activeId }"
          @click="select(p)"
        >
          <div class="item-info">
            <span class="item-name">{{ p.name || p.id }}</span>
            <span class="item-meta">{{ p.modules?.length || 0 }} 模块</span>
          </div>
          <span v-if="p.status" class="item-status" :class="p.status">{{ p.status }}</span>
        </button>
        <div v-if="!filtered.length" class="empty">No projects found</div>
      </div>
      <div class="dropdown-footer">
        <RouterLink to="/onboarding" class="new-project-btn" @click="close">
          <Plus :size="14" /> 新建项目
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.project-selector { position: relative; }
.selector-trigger {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 12px; border-radius: 8px;
  background: var(--bg-secondary); border: 1px solid var(--border);
  cursor: pointer; font-size: 13px; color: var(--text-primary);
}
.selector-trigger:hover { background: var(--bg-hover); }
.project-name { max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rotated { transform: rotate(180deg); transition: transform .2s; }

.backdrop { position: fixed; inset: 0; z-index: 99; }

.selector-dropdown {
  position: absolute; top: 100%; left: 0; margin-top: 4px;
  width: 280px; max-height: 360px;
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,.15);
  z-index: 100; overflow: hidden;
}
.search-input {
  width: 100%; padding: 10px 12px; border: none; border-bottom: 1px solid var(--border);
  background: transparent; color: var(--text-primary); outline: none; font-size: 13px;
}
.project-list { max-height: 260px; overflow-y: auto; }
.project-item {
  display: flex; align-items: center; justify-content: space-between;
  width: 100%; padding: 10px 12px; border: none; background: transparent;
  cursor: pointer; font-size: 13px; color: var(--text-primary);
}
.project-item:hover, .project-item.active { background: var(--bg-secondary); }
.item-info { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; }
.item-name { font-weight: 500; }
.item-meta { font-size: 11px; color: var(--text-muted); }
.item-status { font-size: 10px; padding: 2px 6px; border-radius: 4px; }
.item-status.completed { background: #d4edda; color: #155724; }

.empty { padding: 20px; text-align: center; color: var(--text-muted); font-size: 13px; }
.dropdown-footer { border-top: 1px solid var(--border); padding: 6px; }
.new-project-btn {
  display: flex; align-items: center; gap: 4px; justify-content: center;
  width: 100%; padding: 8px; border-radius: 6px; border: 1px dashed var(--border);
  background: transparent; cursor: pointer; font-size: 12px; color: var(--text-secondary);
  text-decoration: none;
}
.new-project-btn:hover { background: var(--bg-secondary); }
</style>
