/** App Settings — React port. Theme, language, provider, budget. */
import { useSettingsStore } from '../stores/settings'
import { Settings, Palette, Globe, Cpu, DollarSign } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const themes = ['default', 'dusk', 'lime', 'ocean', 'retro', 'neo', 'forest', 'oscura']

export default function SettingsView() {
  const { t, i18n } = useTranslation()
  const app = useSettingsStore(s => s.app)
  const updateApp = useSettingsStore(s => s.updateApp)

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-xl font-bold mb-6 flex items-center gap-2"><Settings size={20} /> {t('settings.title')}</h1>

      <div className="space-y-6">
        {/* Appearance */}
        <Section icon={Palette} title="外观">
          <div className="grid grid-cols-4 gap-2">
            {themes.map(name => (
              <button key={name} onClick={() => { updateApp({ theme: name }); localStorage.setItem('tlo-theme-name', name); document.documentElement.setAttribute('data-theme', name) }}
                className={`px-3 py-2 rounded-lg text-xs font-medium border transition-colors ${app.theme === name ? 'border-primary bg-primary/10 text-primary' : 'border-border hover:bg-accent'}`}>
                {name}
              </button>
            ))}
          </div>
          <label className="flex items-center gap-2 mt-3 text-sm cursor-pointer">
            <input type="checkbox" checked={app.darkMode} onChange={e => { updateApp({ darkMode: e.target.checked }); document.documentElement.classList.toggle('dark', e.target.checked); localStorage.setItem('tlo-theme', e.target.checked ? 'dark' : 'light') }} />
            {t('theme.dark')}
          </label>
        </Section>

        {/* Language */}
        <Section icon={Globe} title={t('lang.label')}>
          <div className="flex gap-2">
            {['zh', 'en'].map(l => (
              <button key={l} onClick={() => { i18n.changeLanguage(l); localStorage.setItem('tlo-lang', l) }}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${i18n.language === l ? 'border-primary bg-primary/10 text-primary' : 'border-border hover:bg-accent'}`}>
                {l === 'zh' ? '中文' : 'English'}
              </button>
            ))}
          </div>
        </Section>

        {/* Provider */}
        <Section icon={Cpu} title={t('settings.provider')}>
          <select value={app.provider} onChange={e => updateApp({ provider: e.target.value })}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-sm">
            {['claude', 'deepseek', 'openai', 'ollama'].map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <div className="mt-2 text-xs text-muted-foreground">Model: {app.defaultModel} | Thinking: {app.thinkingLevel}</div>
        </Section>

        {/* Budget */}
        <Section icon={DollarSign} title="预算">
          <div className="flex items-center gap-4">
            <input type="number" value={app.costBudget} onChange={e => updateApp({ costBudget: +e.target.value })}
              className="w-24 px-3 py-2 border border-border rounded-lg bg-background text-sm" />
            <span className="text-sm text-muted-foreground">USD / 月</span>
          </div>
        </Section>
      </div>
    </div>
  )
}

function Section({ icon: Icon, title, children }: { icon: any; title: string; children: React.ReactNode }) {
  return (
    <div className="glass-card !rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3 text-sm font-semibold">
        <Icon size={16} className="text-primary" /> {title}
      </div>
      {children}
    </div>
  )
}
