<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePreferences } from '@/composables/usePreferences'
import { Languages, Sun, Moon, Palette, Server } from 'lucide-vue-next'

const { t } = useI18n()
const { currentTheme, isDark, lang, themeNames, setTheme, toggleDark, setLang } = usePreferences()

const providers = ['claude', 'deepseek', 'google']
const currentProvider = ref(localStorage.getItem('tlo-provider') || 'claude')
const auditInterval = ref(localStorage.getItem('tlo-audit-interval') || '86400')

function saveProvider() {
  localStorage.setItem('tlo-provider', currentProvider.value)
  localStorage.setItem('tlo-audit-interval', auditInterval.value)
  ;(window as any).__tlo_toast?.add(t('settings.saved'), 'success')
}
</script>

<template>
  <div class="max-w-[560px] space-y-5">
    <!-- Language -->
    <div class="glass-card !rounded-xl p-5">
      <h3 class="text-sm font-semibold mb-4 flex items-center gap-2"><Languages :size="16" :stroke-width="2" class="text-primary" /> {{ t('lang.label') }}</h3>
      <div class="flex gap-2">
        <button
          @click="setLang('zh')"
          :class="['flex-1 py-3 rounded-lg text-sm font-semibold cursor-pointer border transition-all font-sans',
            lang === 'zh' ? 'btn-primary' : 'btn-outline']"
        >🇨🇳 中文</button>
        <button
          @click="setLang('en')"
          :class="['flex-1 py-3 rounded-lg text-sm font-semibold cursor-pointer border transition-all font-sans',
            lang === 'en' ? 'btn-primary' : 'btn-outline']"
        >🇺🇸 English</button>
      </div>
    </div>

    <!-- Appearance -->
    <div class="glass-card !rounded-xl p-5">
      <h3 class="text-sm font-semibold mb-4 flex items-center gap-2"><Palette :size="16" :stroke-width="2" class="text-primary" /> Appearance</h3>

      <!-- Dark/Light -->
      <div class="flex gap-2 mb-4">
        <button @click="toggleDark" :class="['flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-semibold cursor-pointer border transition-all font-sans', !isDark ? 'btn-primary' : 'btn-outline']">
          <Sun :size="15" /> Light
        </button>
        <button @click="toggleDark" :class="['flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-semibold cursor-pointer border transition-all font-sans', isDark ? 'btn-primary' : 'btn-outline']">
          <Moon :size="15" /> Dark
        </button>
      </div>

      <!-- Theme grid -->
      <div class="text-xs text-muted-foreground mb-2.5 font-semibold uppercase tracking-wider">Color Theme</div>
      <div class="grid grid-cols-4 gap-2">
        <button v-for="name in themeNames" :key="name" @click="setTheme(name)"
          :class="['py-2.5 rounded-lg text-xs font-semibold cursor-pointer border transition-all font-sans capitalize',
            currentTheme === name ? 'border-primary text-primary bg-primary/10 shadow-sm' : 'btn-outline opacity-70']"
        >{{ name }}</button>
      </div>
    </div>

    <!-- Provider -->
    <div class="glass-card !rounded-xl p-5">
      <h3 class="text-sm font-semibold mb-4 flex items-center gap-2"><Server :size="16" :stroke-width="2" class="text-primary" /> {{ t('settings.provider') }}</h3>
      <div class="space-y-3.5">
        <div>
          <label class="block text-xs font-semibold mb-1.5 text-muted-foreground">LLM Provider</label>
          <select v-model="currentProvider" class="w-full px-3 py-2.5 rounded-lg border text-sm bg-card text-foreground outline-none focus:border-ring transition-colors font-sans">
            <option v-for="p in providers" :key="p" :value="p">{{ p === 'claude' ? 'Anthropic Claude' : p === 'deepseek' ? 'DeepSeek' : 'Google Gemini' }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold mb-1.5 text-muted-foreground">{{ t('settings.interval') }}</label>
          <input v-model="auditInterval" type="number" class="w-full px-3 py-2.5 rounded-lg border text-sm bg-card text-foreground outline-none focus:border-ring transition-colors font-mono" />
        </div>
        <button @click="saveProvider" class="btn-primary w-full">{{ t('settings.save') }}</button>
      </div>
    </div>
  </div>
</template>
