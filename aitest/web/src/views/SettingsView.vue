<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
const provider = ref(localStorage.getItem('tlo-provider') || 'claude')
const interval = ref(localStorage.getItem('tlo-audit-interval') || '86400')
function save() { localStorage.setItem('tlo-provider', provider.value); localStorage.setItem('tlo-audit-interval', interval.value); (window as any).__tlo_toast?.add(t('settings.saved'), 'success') }
</script>
<template>
  <div class="max-w-[520px]">
    <h2 class="text-base font-semibold mb-5">{{ t('settings.title') }}</h2>
    <div class="glass-card p-5 space-y-4">
      <div>
        <label class="block text-xs font-semibold mb-1.5 text-muted-foreground">{{ t('settings.provider') }}</label>
        <select v-model="provider" class="w-full px-3 py-2.5 rounded-lg border text-sm bg-card text-foreground outline-none focus:border-ring transition-colors font-sans">
          <option value="claude">Anthropic Claude</option>
          <option value="deepseek">DeepSeek</option>
          <option value="google">Google Gemini</option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-semibold mb-1.5 text-muted-foreground">{{ t('settings.interval') }}</label>
        <input v-model="interval" type="number" class="w-full px-3 py-2.5 rounded-lg border text-sm bg-card text-foreground outline-none focus:border-ring transition-colors font-mono" />
      </div>
      <button @click="save" class="btn-primary">{{ t('settings.save') }}</button>
    </div>
  </div>
</template>
