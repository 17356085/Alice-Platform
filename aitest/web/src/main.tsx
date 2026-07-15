import React from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import { I18nextProvider } from 'react-i18next'
import i18n from './i18n'
import App from './App'
import { initMemoryDebug } from './utils/memoryDebug'
import { Toaster } from './lib/toast'
import './styles/tokens.css'
import './styles/themes/all.css'
import './styles/figma-theme.css'

initMemoryDebug()

// Apply persisted visual preferences before React paints to avoid a light-theme
// flash and to keep every route on the same four-theme/mode contract.
try {
  const saved = JSON.parse(localStorage.getItem('tlo-settings') || '{}') as { theme?: string; darkMode?: boolean; language?: string }
  const theme = saved.theme === 'default' || !saved.theme ? 'mahotsukai' : saved.theme
  document.documentElement.setAttribute('data-theme', theme)
  document.documentElement.classList.toggle('dark', saved.darkMode ?? true)
  if (saved.language) void i18n.changeLanguage(saved.language)
} catch { /* use defaults */ }

const isDebug = new URLSearchParams(location.search).has('debug')
if (isDebug) console.log('[boot] React createRoot')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HashRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <I18nextProvider i18n={i18n}>
        <>
          <App />
          <Toaster />
        </>
      </I18nextProvider>
    </HashRouter>
  </React.StrictMode>
)

if (isDebug) console.log('[boot] mounted OK')
