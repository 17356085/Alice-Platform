<script setup lang="ts">
import { ref } from 'vue'

const provider = ref(localStorage.getItem('tlo-provider') || 'claude')
const auditInterval = ref(localStorage.getItem('tlo-audit-interval') || '86400')

function save() {
  localStorage.setItem('tlo-provider', provider.value)
  localStorage.setItem('tlo-audit-interval', auditInterval.value)
  alert('配置已保存')
}
</script>

<template>
  <div class="max-w-[600px]">
    <div class="card bg-card border border-border rounded-lg">
      <div class="px-4 py-3 border-b border-border font-semibold text-[13px]">⚙️ 平台配置</div>
      <div class="p-4 space-y-3.5">
        <div>
          <label class="block text-xs font-semibold mb-1 text-muted-foreground">LLM Provider</label>
          <select v-model="provider" class="w-full max-w-[400px] px-3 py-2 border border-border rounded-md bg-card text-foreground text-[13px] font-sans focus:border-ring focus:shadow-focus outline-none">
            <option value="claude">Anthropic Claude</option>
            <option value="deepseek">DeepSeek</option>
            <option value="google">Google Gemini</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold mb-1 text-muted-foreground">审计间隔 (秒)</label>
          <input v-model="auditInterval" type="number" placeholder="86400" class="w-full max-w-[400px] px-3 py-2 border border-border rounded-md bg-card text-foreground text-[13px] font-sans focus:border-ring outline-none" />
        </div>
        <button @click="save" class="px-5 py-2 bg-primary text-primary-foreground border-none rounded-md text-[13px] cursor-pointer font-sans">保存配置</button>
      </div>
    </div>
  </div>
</template>
