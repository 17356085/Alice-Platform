<script setup lang="ts">
import { ref, computed } from 'vue'
import { useOnboardingStore, type MenuNode } from '@/stores/onboarding'
import { Check, Pencil, X, Plus, Trash2 } from 'lucide-vue-next'

const store = useOnboardingStore()

const editingLabel = ref<string | null>(null)
const editValue = ref('')
const menuItems = computed(() => store.menuTree)

function startEdit(label: string) {
  editingLabel.value = label
  editValue.value = label
}
function saveEdit() {
  if (!editingLabel.value || !editValue.value.trim()) return
  const oldLabel = editingLabel.value
  const newLabel = editValue.value.trim()
  // Update in tree recursively
  function rename(items: MenuNode[]) {
    for (const item of items) {
      if (item.label === oldLabel) item.label = newLabel
      if (item.children) rename(item.children)
    }
  }
  rename(store.menuTree)
  editingLabel.value = null
  editValue.value = ''
}

async function handleConfirm() {
  await store.confirmMenu(store.menuTree)
}
</script>

<template>
  <div class="step-confirm">
    <h3>Review discovered menu structure</h3>
    <p class="subtitle">
      TLO discovered {{ store.menuTree.length }} menu groups from the sidebar.
      Edit labels or remove items before continuing.
    </p>

    <div v-if="!menuItems.length" class="empty">
      <p>No menu items discovered yet. Waiting for scan to complete...</p>
    </div>

    <div v-else class="menu-tree">
      <div v-for="group in menuItems" :key="group.label" class="menu-group">
        <div class="group-header">
          <span class="group-label">{{ group.label }}</span>
          <span v-if="group.children?.length" class="badge">{{ group.children.length }} pages</span>
        </div>

        <ul v-if="group.children?.length" class="page-list">
          <li v-for="page in group.children" :key="page.label" class="page-item">
            <template v-if="editingLabel === page.label">
              <input
                v-model="editValue"
                class="edit-input"
                @keyup.enter="saveEdit"
                @keyup.escape="editingLabel = null"
                autofocus
              />
              <button class="btn-icon save" @click="saveEdit"><Check :size="14" /></button>
              <button class="btn-icon cancel" @click="editingLabel = null"><X :size="14" /></button>
            </template>
            <template v-else>
              <span class="page-label">{{ page.label }}</span>
              <code class="page-route">{{ page.route }}</code>
              <button class="btn-icon edit" @click="startEdit(page.label)">
                <Pencil :size="13" />
              </button>
            </template>
          </li>
        </ul>
      </div>
    </div>

    <div class="actions">
      <p class="note">
        You can edit labels above. Click "Continue" to proceed with page discovery.
      </p>
      <button
        class="btn-confirm"
        :disabled="store.step !== 'confirm_menu'"
        @click="handleConfirm"
      >
        <Check :size="16" />
        Continue with {{ menuItems.length }} groups
      </button>
    </div>
  </div>
</template>

<style scoped>
.step-confirm {
  padding: 16px 0;
}
.step-confirm h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 6px;
}
.subtitle {
  color: var(--muted-foreground);
  font-size: 0.85rem;
  margin: 0 0 20px;
}
.empty {
  text-align: center;
  color: var(--muted-foreground);
  padding: 32px;
}

/* Tree */
.menu-tree {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 420px;
  overflow-y: auto;
}
.menu-group {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
}
.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.group-label {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--foreground);
}
.badge {
  background: var(--primary);
  color: var(--primary-foreground);
  font-size: 0.7rem;
  padding: 1px 8px;
  border-radius: var(--radius-full);
}
.page-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.page-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  transition: background 0.1s;
}
.page-item:hover {
  background: var(--secondary);
}
.page-label {
  font-size: 0.85rem;
  color: var(--foreground);
  flex: 1;
}
.page-route {
  font-size: 0.75rem;
  color: var(--muted-foreground);
  background: var(--secondary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
}
.edit-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid var(--primary);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}
.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
  color: var(--muted-foreground);
}
.btn-icon:hover { background: var(--secondary); }
.btn-icon.save { color: var(--success); }
.btn-icon.cancel { color: var(--destructive); }

/* Actions */
.actions {
  margin-top: 24px;
  text-align: center;
}
.note {
  color: var(--muted-foreground);
  font-size: 0.8rem;
  margin: 0 0 12px;
}
.btn-confirm {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 28px;
  background: var(--success);
  color: var(--success-foreground);
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}
.btn-confirm:hover:not(:disabled) { filter: brightness(1.1); }
.btn-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
