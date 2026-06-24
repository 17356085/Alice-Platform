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

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)
app.mount('#app')
