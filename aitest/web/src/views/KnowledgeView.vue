<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { BookOpen, Database, Brain, Search } from 'lucide-vue-next'

const rag = ref<any>({})
const memory = ref<any>({})
const loading = ref(true)

onMounted(async () => {
  try {
    const [healthResp, metricsResp] = await Promise.all([
      fetch('http://localhost:8000/health'),
      fetch('http://localhost:8000/api/kpi/operational'),
    ])
    if (healthResp.ok) {
      rag.value = (await healthResp.json()).components?.rag || {}
    }
    if (metricsResp.ok) {
      const data = await metricsResp.json()
      memory.value = data.memory || {}
    }
  } catch { /* backend not available */ }
  loading.value = false
})
</script>

<template>
  <div class="knowledge">
    <div class="kn-header">
      <BookOpen :size="20" />
      <h1>知识库</h1>
    </div>

    <!-- ChromaDB stats -->
    <div class="stat-cards">
      <div class="stat-card">
        <Database :size="18" class="stat-icon" />
        <div class="stat-value">{{ rag.collections || '—' }}</div>
        <div class="stat-label">集合</div>
      </div>
      <div class="stat-card">
        <Search :size="18" class="stat-icon" />
        <div class="stat-value">{{ rag.total_docs || '—' }}</div>
        <div class="stat-label">文档</div>
      </div>
      <div class="stat-card" :class="rag.status === 'connected' ? 'green' : 'red'">
        <div class="stat-value">{{ rag.status === 'connected' ? '已连接' : '未连接' }}</div>
        <div class="stat-label">状态</div>
      </div>
    </div>

    <!-- Memory Hit Rate -->
    <div class="section" v-if="Object.keys(memory).length > 0">
      <h2><Brain :size="14" /> Memory 命中率</h2>
      <div class="memory-grid">
        <div v-for="(data, collection) in Object.entries(memory)" :key="collection" class="memory-card">
          <div class="mem-name">{{ collection }}</div>
          <div class="mem-bar-wrap">
            <div class="mem-bar" :style="{ width: Math.round((data as any).hit_rate * 100) + '%' }"></div>
          </div>
          <div class="mem-stats">
            <span>{{ Math.round((data as any).hit_rate * 100) }}% 命中</span>
            <span>{{ (data as any).hits }}/{{ (data as any).total }} 次查询</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && Object.keys(memory).length === 0" class="empty">
      <Brain :size="32" class="muted" />
      <p>暂无 Memory 数据</p>
      <p class="hint">运行 SOP 后，Memory 命中率将在此显示</p>
    </div>

    <!-- Collections list -->
    <div class="section" v-if="rag.names?.length > 0">
      <h2>集合列表</h2>
      <div class="collection-list">
        <div v-for="name in rag.names" :key="name" class="collection-item">
          <Database :size="12" />
          <span>{{ name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.knowledge { padding: 24px 32px; max-width: 1000px; }
.kn-header { display: flex; align-items: center; gap: 10px; margin-bottom: 24px; }
.kn-header h1 { font-size: 19px; font-weight: 700; margin: 0; }

.stat-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 28px; }
.stat-card {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 10px; padding: 18px; text-align: center;
}
.stat-card.green .stat-value { color: #22c55e; }
.stat-card.red .stat-value { color: #ef4444; }
.stat-icon { opacity: .5; margin-bottom: 6px; }
.stat-value { font-size: 24px; font-weight: 700; }
.stat-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

.section { margin-bottom: 28px; }
.section h2 { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; margin-bottom: 14px; }

.memory-grid { display: flex; flex-direction: column; gap: 10px; }
.memory-card {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 10px; padding: 14px;
}
.mem-name { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.mem-bar-wrap { height: 8px; background: var(--bg-secondary); border-radius: 4px; overflow: hidden; margin-bottom: 6px; }
.mem-bar { height: 100%; background: #22c55e; border-radius: 4px; transition: width .5s; }
.mem-stats { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); }

.collection-list { display: flex; flex-wrap: wrap; gap: 8px; }
.collection-item {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; padding: 6px 12px; background: var(--bg-primary);
  border: 1px solid var(--border); border-radius: 6px;
}

.empty { text-align: center; padding: 48px 0; color: var(--text-muted); }
.hint { font-size: 13px; margin-top: 8px; }
.muted { opacity: .3; }
</style>
