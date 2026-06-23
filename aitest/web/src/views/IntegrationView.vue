<script setup lang="ts">
/** GitHub/GitLab Integration — manage connections, view linked issues. */
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '../stores/settings'
import { useProjectStore } from '../stores/project'
import { api } from '../api/client'
import { Github, Gitlab, Link2, CheckCircle, XCircle, ExternalLink } from 'lucide-vue-next'

const settingsStore = useSettingsStore()
const projectStore = useProjectStore()

const activeTab = ref<'github' | 'gitlab'>('github')
const testing = ref(false)
const testResult = ref<{ ok: boolean; message: string } | null>(null)

const projectSettings = computed(() =>
  settingsStore.getProjectSettings(projectStore.activeId)
)

async function testConnection(platform: 'github' | 'gitlab') {
  testing.value = true; testResult.value = null
  try {
    const result = await api.get<{ configured: boolean; note: string }>('/api/integrations/status')
    const configured = platform === 'github' ? result.github?.configured : result.gitlab?.configured
    testResult.value = {
      ok: true,
      message: configured ? '连接成功' : 'Token未配置或无效。请在项目设置→集成中配置。',
    }
  } catch (e: any) {
    testResult.value = { ok: false, message: e.message }
  } finally { testing.value = false }
}

onMounted(() => { /* auto-check status */ })
</script>

<template>
  <div class="integration-view">
    <h1><Link2 :size="22" /> 项目集成</h1>

    <div class="tab-bar">
      <button :class="['tab-btn', { active: activeTab === 'github' }]" @click="activeTab = 'github'">
        <Github :size="16" /> GitHub
      </button>
      <button :class="['tab-btn', { active: activeTab === 'gitlab' }]" @click="activeTab = 'gitlab'">
        <Gitlab :size="16" /> GitLab
      </button>
    </div>

    <!-- GitHub tab -->
    <div v-if="activeTab === 'github'" class="tab-content">
      <div class="card">
        <h3>GitHub 集成状态</h3>
        <div class="status-row">
          <Github :size="20" />
          <span class="status-label">Token:</span>
          <span v-if="projectSettings.githubToken" class="status-ok"><CheckCircle :size="14" /> 已配置</span>
          <span v-else class="status-missing"><XCircle :size="14" /> 未配置</span>
        </div>
        <div class="status-row">
          <span class="status-label">Repo:</span>
          <span v-if="projectSettings.githubRepo" class="status-value">{{ projectSettings.githubRepo }}</span>
          <span v-else class="status-missing">未设置</span>
        </div>
        <button class="test-btn" :disabled="testing" @click="testConnection('github')">
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
        <p v-if="testResult" :class="['test-result', testResult.ok ? 'success' : 'error']">
          {{ testResult.message }}
        </p>
      </div>

      <div class="card">
        <h3>Issue 自动创建</h3>
        <p class="hint">当测试失败时，自动在 GitHub 创建 Issue。</p>
        <label class="toggle-row">
          <span>测试失败 → 自动创建 Issue</span>
          <input type="checkbox" class="toggle" />
        </label>
        <label class="toggle-row">
          <span>包含失败截图</span>
          <input type="checkbox" class="toggle" />
        </label>
      </div>

      <div class="card">
        <h3>设置</h3>
        <p class="hint">Token 和 Repo 在 <router-link to="/workspace/settings">项目设置 → 集成</router-link> 中配置。</p>
      </div>
    </div>

    <!-- GitLab tab -->
    <div v-if="activeTab === 'gitlab'" class="tab-content">
      <div class="card">
        <h3>GitLab 集成状态</h3>
        <div class="status-row">
          <Gitlab :size="20" />
          <span class="status-label">Token:</span>
          <span v-if="projectSettings.gitlabToken" class="status-ok"><CheckCircle :size="14" /> 已配置</span>
          <span v-else class="status-missing"><XCircle :size="14" /> 未配置</span>
        </div>
        <div class="status-row">
          <span class="status-label">Project ID:</span>
          <span v-if="projectSettings.gitlabProject" class="status-value">{{ projectSettings.gitlabProject }}</span>
          <span v-else class="status-missing">未设置</span>
        </div>
        <button class="test-btn" :disabled="testing" @click="testConnection('gitlab')">
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
        <p v-if="testResult" :class="['test-result', testResult.ok ? 'success' : 'error']">
          {{ testResult.message }}
        </p>
      </div>

      <div class="card">
        <h3>设置</h3>
        <p class="hint">Token 和 Project ID 在 <router-link to="/workspace/settings">项目设置 → 集成</router-link> 中配置。</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.integration-view { padding: 24px 32px; max-width: 640px; }
.integration-view h1 { display: flex; align-items: center; gap: 10px; font-size: 20px; font-weight: 700; margin: 0 0 20px; }

.tab-bar { display: flex; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
.tab-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 16px; border: none; background: transparent;
  cursor: pointer; font-size: 13px; color: var(--text-secondary);
  border-bottom: 2px solid transparent; transition: all .15s;
}
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-btn:hover { color: var(--text-primary); }

.tab-content { display: flex; flex-direction: column; gap: 12px; }
.card {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px;
}
.card h3 { font-size: 14px; font-weight: 600; margin: 0 0 12px; }
.hint { font-size: 12px; color: var(--text-muted); margin: 0 0 8px; }

.status-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 13px; }
.status-label { color: var(--text-secondary); width: 50px; }
.status-ok { display: flex; align-items: center; gap: 4px; color: #22c55e; }
.status-missing { display: flex; align-items: center; gap: 4px; color: var(--text-muted); }
.status-value { color: var(--text-primary); font-family: monospace; }

.test-btn {
  padding: 8px 16px; border: 1px solid var(--border); border-radius: 8px;
  background: var(--bg-primary); cursor: pointer; font-size: 13px; margin-top: 8px;
}
.test-btn:hover { background: var(--bg-secondary); }
.test-result { margin-top: 8px; padding: 8px 12px; border-radius: 6px; font-size: 12px; }
.test-result.success { background: #d4edda; color: #155724; }
.test-result.error { background: #fef2f2; color: #991b1b; }

.toggle-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; font-size: 13px; }
</style>
