<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import TerminalPanel from '@/components/TerminalPanel.vue'
const { t } = useI18n()
</script>
<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <span class="text-xs text-muted-foreground">{{ t('execution.title') }}</span>
      <button class="btn-outline text-xs">{{ t('execution.refresh') }}</button>
    </div>
    <TerminalPanel auto-connect />
    <div class="mt-4 text-xs text-muted-foreground text-center">{{ t('execution.footer') }}</div>
  </div>
</template>
