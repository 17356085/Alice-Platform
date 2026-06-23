<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Globe, FolderOpen, FileCode, CheckCircle, AlertTriangle, Loader2 } from 'lucide-vue-next'
import { api } from '../../api/client'
import { ENDPOINTS } from '../../api/endpoints'

const { t } = useI18n()

const emit = defineEmits<{
  choose: [sourceType: 'url' | 'local', value: string]
}>()

const selected = ref<'url' | 'local'>('url')
const urlValue = ref('https://')
const projectPath = ref('')
const pathError = ref('')
const pathValidating = ref(false)

// Path validation result
interface PathResult {
  valid: boolean; exists: boolean; has_package_json: boolean
  framework: string; framework_version: string; ui_library: string
  typescript: boolean; suggestions: string[]; error: string
}
const pathResult = ref<PathResult | null>(null)

function selectUrl() { selected.value = 'url'; pathError.value = ''; pathResult.value = null }
function selectLocal() { selected.value = 'local'; pathError.value = '' }

const frameworkLabel = computed(() => {
  if (!pathResult.value) return ''
  const r = pathResult.value
  if (r.framework === 'unknown') return '⚠️ 未识别框架 (将跳过源码分析)'
  if (r.framework === 'error') return '⚠️ 检测异常'
  let label = `✅ ${r.framework}`
  if (r.framework_version) label += ` ${r.framework_version}`
  if (r.ui_library) label += ` + ${r.ui_library}`
  if (r.typescript) label += ' + TS'
  return label
})

async function validatePath() {
  const raw = projectPath.value.trim()
  if (!raw) {
    pathError.value = t('onboarding.invalid_path')
    return false
  }
  pathValidating.value = true
  pathError.value = ''
  pathResult.value = null

  try {
    const result = await api.post<PathResult>(ENDPOINTS.ONBOARDING_VALIDATE, { project_path: raw })
    pathResult.value = result
    if (!result.exists) {
      pathError.value = result.error || '路径不存在'
      return false
    }
    if (!result.has_package_json) {
      pathError.value = result.error || '未找到 package.json'
      return false
    }
    return true
  } catch (e: any) {
    pathError.value = `验证失败: ${e.message}`
    return false
  } finally {
    pathValidating.value = false
  }
}

async function handleContinue() {
  if (selected.value === 'url') {
    if (!urlValue.value || !urlValue.value.startsWith('http')) {
      pathError.value = t('onboarding.invalid_url')
      return
    }
    emit('choose', 'url', urlValue.value)
  } else {
    const valid = await validatePath()
    if (!valid) return
    emit('choose', 'local', projectPath.value.trim())
  }
}

async function browseFolder() {
  if ('showDirectoryPicker' in window) {
    try {
      const handle = await (window as any).showDirectoryPicker()
      // Try non-standard path property first (some Chromium builds expose it)
      projectPath.value = handle.path || handle.name || ''
      if (!handle.path) {
        pathError.value = `已选择 "${handle.name}"，请手动补全完整路径（如 D:\\Desktop\\${handle.name}）`
      }
    } catch {
      // User cancelled
    }
  } else {
    // Fallback: use webkitdirectory input
    const input = document.createElement('input')
    input.type = 'file'
    ;(input as any).webkitdirectory = true
    input.onchange = (e: any) => {
      if (e.target.files?.length) {
        const rel = e.target.files[0].webkitRelativePath
        const folder = rel.split('/')[0]
        projectPath.value = folder
        pathError.value = `已选择 "${folder}"，请手动补全完整路径（如 D:\\Desktop\\${folder}）`
      }
    }
    input.click()
  }
}
</script>

<template>
  <div class="step-choose">
    <h3>{{ t('onboarding.choose_title') }}</h3>

    <div class="source-cards">
      <button class="source-card" :class="{ selected: selected === 'url' }" @click="selectUrl">
        <Globe :size="32" />
        <div class="card-text">
          <strong>{{ t('onboarding.url_option') }}</strong>
          <span class="desc">{{ t('onboarding.url_desc') }}</span>
        </div>
      </button>

      <button class="source-card" :class="{ selected: selected === 'local' }" @click="selectLocal">
        <FolderOpen :size="32" />
        <div class="card-text">
          <strong>{{ t('onboarding.local_option') }}</strong>
          <span class="desc">{{ t('onboarding.local_desc') }}</span>
        </div>
      </button>

      <button class="source-card disabled" disabled>
        <FileCode :size="32" />
        <div class="card-text">
          <strong>Import API spec</strong>
          <span class="desc">OpenAPI/Swagger — coming soon</span>
        </div>
      </button>
    </div>

    <!-- URL input -->
    <div v-if="selected === 'url'" class="input-area">
      <label><Globe :size="14" /> Application URL</label>
      <input v-model="urlValue" type="url" :placeholder="t('onboarding.url_placeholder')" @keyup.enter="handleContinue" />
    </div>

    <!-- Local path input -->
    <div v-if="selected === 'local'" class="input-area">
      <label><FolderOpen :size="14" /> Project path</label>
      <div class="path-row">
        <input
          v-model="projectPath" type="text"
          :placeholder="t('onboarding.path_placeholder')"
          @keyup.enter="handleContinue"
          @input="pathResult = null; pathError = ''"
        />
        <button class="btn-browse" @click="browseFolder">{{ t('onboarding.browse') }}</button>
      </div>

      <!-- Validation status -->
      <div v-if="pathValidating" class="status-row validating">
        <Loader2 :size="14" class="spin" /> 正在验证项目路径...
      </div>
      <div v-else-if="pathResult?.valid" class="status-row success">
        <CheckCircle :size="14" /> {{ frameworkLabel }}
      </div>
      <div v-else-if="pathResult && !pathResult?.has_package_json" class="status-row warning">
        <AlertTriangle :size="14" /> {{ pathError }}
        <div v-if="pathResult.suggestions.length" class="suggestions">
          <p v-for="s in pathResult.suggestions" :key="s">{{ s }}</p>
        </div>
      </div>

      <p class="hint">支持: Vue 3/2 (vue-router), React, Next.js, Nuxt, Angular</p>
    </div>

    <!-- Error -->
    <p v-if="pathError && !pathResult" class="error-msg">{{ pathError }}</p>

    <button class="btn-continue" :disabled="pathValidating" @click="handleContinue">
      <Loader2 v-if="pathValidating" :size="14" class="spin" />
      {{ t('onboarding.continue') }}
    </button>
  </div>
</template>

<style scoped>
.step-choose { padding: 16px 0; }
.step-choose h3 { font-size: 1.05rem; font-weight: 600; margin: 0 0 20px; color: var(--foreground); }

.source-cards { display: flex; flex-direction: column; gap: 10px; margin-bottom: 24px; }
.source-card {
  display: flex; align-items: center; gap: 14px; padding: 16px;
  background: var(--card); border: 2px solid var(--border); border-radius: var(--radius-lg);
  cursor: pointer; text-align: left; transition: border-color .15s, box-shadow .15s;
  font-family: inherit; color: var(--foreground);
}
.source-card:hover:not(.disabled) { border-color: var(--primary); }
.source-card.selected { border-color: var(--primary); box-shadow: var(--shadow-focus); }
.source-card.disabled { opacity: .4; cursor: not-allowed; }
.card-text { display: flex; flex-direction: column; gap: 2px; }
.card-text strong { font-size: .9rem; }
.desc { font-size: .78rem; color: var(--muted-foreground); }

.input-area { margin-bottom: 16px; }
.input-area label { display: flex; align-items: center; gap: 6px; font-size: .82rem; font-weight: 600; color: var(--foreground); margin-bottom: 6px; }
.input-area input { width: 100%; padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--card); color: var(--foreground); font-size: .9rem; }
.input-area input:focus { outline: none; border-color: var(--primary); box-shadow: var(--shadow-focus); }

.path-row { display: flex; gap: 8px; }
.path-row input { flex: 1; }
.btn-browse { padding: 10px 16px; background: var(--secondary); color: var(--secondary-foreground); border: 1px solid var(--border); border-radius: var(--radius-md); cursor: pointer; font-size: .85rem; white-space: nowrap; }
.btn-browse:hover { background: var(--primary); color: var(--primary-foreground); }

.hint { color: var(--muted-foreground); font-size: .75rem; margin: 4px 0 0; }

.status-row { display: flex; align-items: flex-start; gap: 6px; margin-top: 8px; padding: 8px 12px; border-radius: var(--radius-md); font-size: .8rem; }
.status-row.validating { background: var(--secondary); color: var(--secondary-foreground); }
.status-row.success { background: #d4edda; color: #155724; }
.status-row.warning { background: #fff3cd; color: #856404; flex-direction: column; }
.suggestions { margin-top: 4px; }
.suggestions p { margin: 2px 0; font-size: .75rem; opacity: .85; }

.error-msg { color: var(--destructive); font-size: .82rem; margin: 8px 0; }

.btn-continue {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 28px; background: var(--primary); color: var(--primary-foreground);
  border: none; border-radius: var(--radius-md); font-size: .9rem; font-weight: 600; cursor: pointer; margin-top: 8px;
}
.btn-continue:disabled { opacity: .6; cursor: not-allowed; }
.btn-continue:hover:not(:disabled) { filter: brightness(1.1); }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
