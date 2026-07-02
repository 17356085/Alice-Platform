import React from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import { I18nextProvider } from 'react-i18next'
import i18n from './i18n'
import App from './App'
import { initMemoryDebug } from './utils/memoryDebug'
import './styles/tokens.css'
import './styles/themes/all.css'

initMemoryDebug()

const isDebug = new URLSearchParams(location.search).has('debug')
if (isDebug) console.log('[boot] React createRoot')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HashRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <I18nextProvider i18n={i18n}>
        <App />
      </I18nextProvider>
    </HashRouter>
  </React.StrictMode>
)

if (isDebug) console.log('[boot] mounted OK')
