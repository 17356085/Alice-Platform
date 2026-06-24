<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { FolderOpen, FileText, Eye, Download } from 'lucide-vue-next'

const route = useRoute()
const projectId = computed(() => route.params.id as string)
const moduleFilter = ref(route.query.module as string || '')

interface ArtifactItem {
  name: string
  path: string
  exists: boolean
  size?: string
  updated?: string
}

const artifacts = ref<ArtifactItem[]>([])
const previewContent = ref('')
const previewName = ref('')
const loading = ref(false)

async function fetchArtifacts() {
  loading.value = true
  try {
    let url = `http://localhost:8000/api/artifacts/${projectId.value}`
    if (moduleFilter.value) url += `?module=${moduleFilter.value}`
    const resp = await fetch(url)
    if (resp.ok) {
      const data = await resp.json()
      artifacts.value = (data.artifacts || []).map((a: any) => ({
        name: a.name,
        path: a.path,
        exists: a.exists,
        size: a.size ? `${(a.size / 1024).toFixed(1)} KB` : undefined,
        updated: a.updated,
      }))
    }
  } catch {
    artifacts.value = []
  } finally {
    loading.value = false
  }
}

function preview(artifact: ArtifactItem) {
  previewName.value = artifact.name
  previewContent.value = artifact.exists
    ? `# ${artifact.name}\n\n路径: ${artifact.path}\n\n(内容将从后端加载)`
    : '文件尚未生成 — 运行对应 SOP Phase 后自动创建。'
}

onMounted(fetchArtifacts)
</script>

<template>
  <div class="artifacts">
    <div class="art-header">
      <div class="header-left">
        <FolderOpen :size="20" />
        <h1>产物 — {{ projectId }}</h1>
      </div>
      <div class="filter-row">
        <input v-model="moduleFilter" placeholder="模块过滤..." class="filter-input" @change="fetchArtifacts" />
      </div>
    </div>

    <div v-if="loading" class="muted">加载中...</div>
    <div v-else class="art-layout">
      <!-- File list -->
      <div class="file-list">
        <div
          v-for="art in artifacts"
          :key="art.path"
          class="file-item"
          :class="{ missing: !art.exists }"
          @click="preview(art)"
        >
          <FileText :size="14" :class="art.exists ? 'green' : 'muted'" />
          <span class="file-name">{{ art.name }}</span>
          <span class="file-path">{{ art.path }}</span>
          <span v-if="art.exists" class="badge-ok">✓</span>
          <span v-else class="badge-missing">—</span>
        </div>
      </div>

      <!-- Preview panel -->
      <div class="preview-panel">
        <div class="preview-header">
          <Eye :size="14" />
          <span>{{ previewName || '选择文件预览' }}</span>
        </div>
        <div class="preview-body">
          <pre v-if="previewContent">{{ previewContent }}</pre>
          <div v-else class="empty-preview">
            <FolderOpen :size="32" class="muted" />
            <p>选择一个产物文件查看内容</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.artifacts { padding: 24px 32px; max-width: 1400px; }
.art-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.header-left h1 { font-size: 19px; font-weight: 700; margin: 0; }
.filter-input { font-size: 13px; padding: 6px 12px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); width: 200px; }

.art-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; min-height: 400px; }
.file-list { display: flex; flex-direction: column; gap: 2px; }
.file-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; border-radius: 6px; cursor: pointer;
  transition: background .1s;
}
.file-item:hover { background: var(--bg-secondary); }
.file-item.missing { opacity: .5; }
.file-name { font-size: 13px; font-weight: 500; flex: 1; }
.file-path { font-size: 11px; color: var(--text-muted); font-family: monospace; }
.badge-ok { color: #22c55e; font-size: 12px; }
.badge-missing { color: var(--text-muted); font-size: 12px; }

.preview-panel {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 10px; overflow: hidden;
}
.preview-header {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; background: var(--bg-secondary);
  font-size: 13px; font-weight: 600;
}
.preview-body { padding: 16px; overflow: auto; max-height: 500px; }
.preview-body pre { font-size: 13px; line-height: 1.6; white-space: pre-wrap; }
.empty-preview { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 48px; color: var(--text-muted); gap: 8px; }

.muted { color: var(--text-muted); font-size: 13px; }
.green { color: #22c55e; }
</style>
