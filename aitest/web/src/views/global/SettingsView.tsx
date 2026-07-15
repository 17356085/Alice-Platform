/** App Settings — shadcn/ui edition. Theme, language, provider, budget. */
import { useSettingsStore } from '../../stores/settings'
import { Settings, Palette, Globe, Cpu, DollarSign } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { PageHeader } from '@/components/shared'

const themes = [
  { value: 'mahotsukai', label: 'Mahotsukai — Midnight Blue' },
  { value: 'alice', label: 'Alice — Midnight Iris' },
  { value: 'aoko', label: 'Aoko — Clear Sky' },
  { value: 'soujuurou', label: 'Soujuurou — Mountain Wood' },
]

export default function SettingsView() {
  const { t, i18n } = useTranslation()
  const app = useSettingsStore(s => s.app)
  const updateApp = useSettingsStore(s => s.updateApp)

  const applyTheme = (name: string) => {
    updateApp({ theme: name })
    localStorage.setItem('tlo-theme-name', name)
    document.documentElement.setAttribute('data-theme', name)
  }

  const applyDark = (checked: boolean) => {
    updateApp({ darkMode: checked })
    document.documentElement.classList.toggle('dark', checked)
    localStorage.setItem('tlo-theme', checked ? 'dark' : 'light')
  }

  const applyLang = (lang: string) => {
    i18n.changeLanguage(lang)
    localStorage.setItem('tlo-lang', lang)
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 p-4 sm:p-6">
      <PageHeader eyebrow="Workspace preferences" title={t('settings.title')} description="管理主题、语言、模型提供方和成本预算。设置会保存在本地工作区。" />

      <div className="flex flex-col gap-4">
        {/* Appearance */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Palette size={16} className="text-primary" /> 外观
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <ToggleGroup type="single" value={app.theme} onValueChange={v => v && applyTheme(v)}
              className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {themes.map(t => (
                <ToggleGroupItem key={t.value} value={t.value} className="text-xs h-8">
                  {t.label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
            <div className="flex items-center gap-2">
              <Checkbox id="dark-mode" checked={app.darkMode}
                onCheckedChange={v => applyDark(v === true)} />
              <Label htmlFor="dark-mode" className="cursor-pointer text-sm">
                {t('theme.dark')}
              </Label>
            </div>
          </CardContent>
        </Card>

        {/* Language */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Globe size={16} className="text-primary" /> {t('lang.label')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ToggleGroup type="single" value={i18n.language} onValueChange={v => v && applyLang(v)}>
              <ToggleGroupItem value="zh" className="text-sm">中文</ToggleGroupItem>
              <ToggleGroupItem value="en" className="text-sm">English</ToggleGroupItem>
            </ToggleGroup>
          </CardContent>
        </Card>

        {/* Provider */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Cpu size={16} className="text-primary" /> {t('settings.provider')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Select value={app.provider} onValueChange={v => updateApp({ provider: v })}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {['claude', 'deepseek', 'openai', 'ollama'].map(p => (
                  <SelectItem key={p} value={p}>{p}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="mt-2 text-xs text-muted-foreground">
              Model: {app.defaultModel} · Thinking: {app.thinkingLevel}
            </p>
          </CardContent>
        </Card>

        {/* Budget */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <DollarSign size={16} className="text-primary" /> 预算
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-4">
            <Input type="number" value={app.costBudget}
              onChange={e => updateApp({ costBudget: +e.target.value })}
              className="w-24" />
            <span className="text-sm text-muted-foreground">USD / 月</span>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
