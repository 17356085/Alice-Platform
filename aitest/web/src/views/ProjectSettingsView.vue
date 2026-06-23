<script setup lang="ts">
/** Project-level settings — per Aperant's settings project tab pattern.

Visible only when a project is active. Covers: General, Provider override, Integrations.
*/
import { ref, computed } from 'vue'
import { useProjectStore } from '../stores/project'
import { useSettingsStore, type ProjectSettings } from '../stores/settings'
import { FolderOpen, Globe, Key, GitBranch, Link } from 'lucide-vue-next'

const projectStore = useProjectStore()
const settingsStore = useSettingsStore()

const activeTab = ref<'general' | 'provider' | 'integrations'>('general')

const projectSettings = computed(() =>
  settingsStore.getProjectSettings(projectStore.activeId)
)

const form = ref<ProjectSettings>({ ...projectSettings.value })

function save() {
  settingsStore.updateProject(projectStore.activeId, { ...form.value })
}

// ── Tabs ──────────────────────────────────────────────────

const tabs = [
  { id: 'general' as const,      label: '通用', icon: FolderOpen },
  { id: 'provider' as const,     label: 'Provider', icon: Globe },
  { id: 'integrations' as const, label: '集成', icon: Link },
]
</script>

<template>
  <div class="project-settings">
    <div class="settings-header">
      <h1>项目设置</h1>
      <span class="project-name">{{ projectStore.activeProject?.name || projectStore.activeProject?.id }}</span>
    </div>

    <!-- Tab bar -->
    <div class="tab-bar">
      <button v-for="tab in tabs" :key="tab.id"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
        class="tab-btn"
      >
        <component :is="tab.icon" :size="16" />
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <!-- Tab: General -->
    <div v-if="activeTab === 'general'" class="tab-content">
      <label class="field">
        <span>并行任务数</span>
        <input v-model.number="form.maxParallel" type="number" min="1" max="12" class="input" />
      </label>
      <label class="field">
        <span>主分支</span>
        <input v-model="form.mainBranch" type="text" class="input" />
      </label>
    </div>

    <!-- Tab: Provider -->
    <div v-if="activeTab === 'provider'" class="tab-content">
      <p class="hint">覆盖全局 Provider 设置（可选）</p>
      <label class="field">
        <span>Provider</span>
        <select v-model="form.provider" class="input">
          <option value="">使用全局设置</option>
          <option value="claude">Claude</option>
          <option value="deepseek">DeepSeek</option>
          <option value="openai">OpenAI</option>
        </select>
      </label>
      <label class="field">
        <span>模型</span>
        <input v-model="form.model" type="text" class="input" placeholder="使用全局设置" />
      </label>
    </div>

    <!-- Tab: Integrations -->
    <div v-if="activeTab === 'integrations'" class="tab-content">
      <div class="integration-section">
        <h3><span class="icon">🐙</span> GitHub</h3>
        <label class="field">
          <span>Token</span>
          <input v-model="form.githubToken" type="password" class="input" placeholder="ghp_..." />
        </label>
        <label class="field">
          <span>Repo</span>
          <input v-model="form.githubRepo" type="text" class="input" placeholder="owner/repo" />
        </label>
      </div>
      <div class="integration-section">
        <h3><span class="icon">🦊</span> GitLab</h3>
        <label class="field">
          <span>Token</span>
          <input v-model="form.gitlabToken" type="password" class="input" placeholder="glpat-..." />
        </label>
        <label class="field">
          <span>Project ID</span>
          <input v-model="form.gitlabProject" type="text" class="input" />
        </label>
      </div>
    </div>

    <button @click="save" class="save-btn">保存项目设置</button>
  </div>
</template>

<style scoped>
.project-settings { padding: 24px 32px; max-width: 640px; }
.settings-header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 20px; }
.settings-header h1 { font-size: 20px; font-weight: 700; margin: 0; }
.project-name { font-size: 13px; color: var(--text-muted); }

.tab-bar { display: flex; gap: 0; margin-bottom: 24px; border-bottom: 1px solid var(--border); }
.tab-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 16px; border: none; background: transparent;
  cursor: pointer; font-size: 13px; color: var(--text-secondary);
  border-bottom: 2px solid transparent; transition: all .15s;
}
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-btn:hover { color: var(--text-primary); }

.tab-content { margin-bottom: 24px; }
.hint { font-size: 12px; color: var(--text-muted); margin-bottom: 16px; }

.field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 16px; }
.field span { font-size: 12px; font-weight: 600; color: var(--text-secondary); }
.input {
  padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px;
  background: var(--bg-primary); color: var(--text-primary); font-size: 13px;
  outline: none;
}
.input:focus { border-color: var(--accent); }

.integration-section { margin-bottom: 20px; }
.integration-section h3 { display: flex; align-items: center; gap: 6px; font-size: 14px; margin-bottom: 12px; }
.icon { font-size: 16px; }

.save-btn {
  padding: 10px 24px; background: var(--accent); color: #fff;
  border: none; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600;
}
.save-btn:hover { opacity: .9; }
</style>
