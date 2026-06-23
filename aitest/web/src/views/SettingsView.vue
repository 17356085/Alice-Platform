<script setup lang="ts">
/** App-level settings — tabbed per Aperant's AppSettings pattern.

Tabs: Appearance | Provider | Agent | Notifications | Audit
Project-level settings → ProjectSettingsView (workspace/settings)
*/
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSettingsStore } from '../stores/settings'
import { Palette, Globe, Bot, Bell, BarChart3, Trash2 } from 'lucide-vue-next'
import { usePreferences } from '../composables/usePreferences'

const { locale } = useI18n()
const settings = useSettingsStore()
const { currentTheme, isDark, themeNames, setTheme, toggleDark, setLang } = usePreferences()

const activeTab = ref<'appearance' | 'provider' | 'agent' | 'notifications' | 'audit'>('appearance')

const tabs = [
  { id: 'appearance' as const,    icon: Palette,   label: '外观' },
  { id: 'provider' as const,      icon: Globe,     label: 'Provider' },
  { id: 'agent' as const,         icon: Bot,       label: 'Agent' },
  { id: 'notifications' as const, icon: Bell,      label: '通知' },
  { id: 'audit' as const,         icon: BarChart3, label: '审计' },
]

const availableProviders = ['claude', 'deepseek', 'openai', 'ollama']
</script>

<template>
  <div class="settings-page">
    <h1 class="page-title">应用设置</h1>

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

    <!-- Appearance -->
    <div v-if="activeTab === 'appearance'" class="tab-content">
      <div class="card">
        <h3>语言</h3>
        <div class="btn-row">
          <button @click="setLang('zh')" :class="['lang-btn', locale === 'zh' ? 'active' : '']">🇨🇳 中文</button>
          <button @click="setLang('en')" :class="['lang-btn', locale === 'en' ? 'active' : '']">🇺🇸 English</button>
        </div>
      </div>
      <div class="card">
        <h3>模式</h3>
        <div class="btn-row">
          <button @click="toggleDark" :class="['lang-btn', !isDark ? 'active' : '']">☀️ 亮色</button>
          <button @click="toggleDark" :class="['lang-btn', isDark ? 'active' : '']">🌙 暗色</button>
        </div>
      </div>
      <div class="card">
        <h3>颜色主题</h3>
        <div class="theme-grid">
          <button v-for="name in themeNames" :key="name" @click="setTheme(name)"
            :class="['theme-dot', currentTheme === name ? 'active' : '']"
          >{{ name }}</button>
        </div>
      </div>
      <div class="card">
        <h3>UI 缩放</h3>
        <input v-model.number="settings.app.uiScale" type="range" min="75" max="200" step="5" class="slider" />
        <span class="range-value">{{ settings.app.uiScale }}%</span>
      </div>
    </div>

    <!-- Provider -->
    <div v-if="activeTab === 'provider'" class="tab-content">
      <div class="card">
        <h3>主 Provider</h3>
        <select v-model="settings.app.provider" class="select">
          <option v-for="p in availableProviders" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>
      <div class="card">
        <h3>回退链</h3>
        <p class="hint">Provider 不可用时按顺序回退</p>
        <div v-for="(p, i) in settings.app.fallbackChain" :key="i" class="fallback-row">
          <span class="fallback-idx">{{ i + 1 }}</span>
          <select v-model="settings.app.fallbackChain[i]" class="select flex-1">
            <option v-for="ap in availableProviders" :key="ap" :value="ap">{{ ap }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Agent -->
    <div v-if="activeTab === 'agent'" class="tab-content">
      <div class="card">
        <h3>默认模型</h3>
        <input v-model="settings.app.defaultModel" type="text" class="input" placeholder="claude-sonnet-4-6" />
      </div>
      <div class="card">
        <h3>Thinking 级别</h3>
        <select v-model="settings.app.thinkingLevel" class="select">
          <option value="low">Low — 快速响应</option>
          <option value="medium">Medium — 平衡</option>
          <option value="high">High — 深度推理</option>
        </select>
      </div>
    </div>

    <!-- Notifications -->
    <div v-if="activeTab === 'notifications'" class="tab-content">
      <div class="card">
        <label class="toggle-row">
          <span>构建完成通知</span>
          <input v-model="settings.app.notifyBuildComplete" type="checkbox" class="toggle" />
        </label>
      </div>
      <div class="card">
        <label class="toggle-row">
          <span>API 限流告警</span>
          <input v-model="settings.app.notifyRateLimit" type="checkbox" class="toggle" />
        </label>
      </div>
    </div>

    <!-- Audit -->
    <div v-if="activeTab === 'audit'" class="tab-content">
      <div class="card">
        <h3>审计间隔 (秒)</h3>
        <input v-model.number="settings.app.auditInterval" type="number" min="60" step="60" class="input" />
      </div>
      <div class="card">
        <h3>月度成本预算 (USD)</h3>
        <input v-model.number="settings.app.costBudget" type="number" min="1" max="500" class="input" />
      </div>
    </div>

    <!-- Reset -->
    <div class="danger-zone">
      <button @click="settings.resetApp()" class="reset-btn">
        <Trash2 :size="14" /> 重置所有设置
      </button>
    </div>
  </div>
</template>

<style scoped>
.settings-page { padding: 24px 32px; max-width: 560px; }
.page-title { font-size: 20px; font-weight: 700; margin: 0 0 20px; }

.tab-bar { display: flex; gap: 0; margin-bottom: 24px; border-bottom: 1px solid var(--border); overflow-x: auto; }
.tab-btn {
  display: flex; align-items: center; gap: 6px; flex-shrink: 0;
  padding: 10px 14px; border: none; background: transparent;
  cursor: pointer; font-size: 13px; color: var(--text-secondary);
  border-bottom: 2px solid transparent; transition: all .15s;
}
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }

.tab-content { display: flex; flex-direction: column; gap: 12px; }
.card {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px;
}
.card h3 { font-size: 13px; font-weight: 600; margin: 0 0 10px; }
.hint { font-size: 11px; color: var(--text-muted); margin: 0 0 8px; }

.btn-row { display: flex; gap: 8px; }
.lang-btn {
  flex: 1; padding: 10px; border-radius: 8px; border: 1px solid var(--border);
  background: transparent; cursor: pointer; font-size: 13px; font-weight: 600;
  transition: all .15s;
}
.lang-btn.active { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, transparent); }

.theme-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.theme-dot {
  padding: 8px; border-radius: 8px; border: 1px solid var(--border);
  background: transparent; cursor: pointer; font-size: 12px; font-weight: 600;
  text-transform: capitalize; transition: all .15s;
}
.theme-dot.active { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, transparent); }

.slider { width: 100%; }
.range-value { font-size: 13px; font-weight: 600; }

.select, .input {
  width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px;
  background: var(--bg-primary); color: var(--text-primary); font-size: 13px; outline: none;
}
.select:focus, .input:focus { border-color: var(--accent); }

.fallback-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.fallback-idx { font-size: 11px; color: var(--text-muted); width: 16px; text-align: center; }

.toggle-row { display: flex; align-items: center; justify-content: space-between; font-size: 13px; cursor: pointer; }

.danger-zone { margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border); }
.reset-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 16px; border: 1px solid #ef4444; border-radius: 8px;
  background: transparent; color: #ef4444; cursor: pointer; font-size: 12px;
}
.reset-btn:hover { background: #fef2f2; }
</style>
