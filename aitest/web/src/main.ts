import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import { router } from './router'
import { initMemoryDebug } from './utils/memoryDebug'
import './styles/tokens.css'
import './styles/themes/all.css'
import zh from './locales/zh.json'
import en from './locales/en.json'

// ── Diagnostic: ?debug=1 enables memory/DOM overlay ──
initMemoryDebug()

// i18n init
const savedLang = localStorage.getItem('tlo-lang') || 'zh'
const i18n = createI18n({ legacy: false, locale: savedLang, fallbackLocale: 'en', messages: { zh, en } })

console.log('[boot] createApp start')
const app = createApp(App)
console.log('[boot] pinia')
app.use(createPinia())
console.log('[boot] router')
app.use(router)
console.log('[boot] i18n')
app.use(i18n)
console.log('[boot] mount')
app.mount('#app')
console.log('[boot] mounted OK')
