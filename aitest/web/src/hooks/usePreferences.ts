/** Theme/language preferences hook — React port.
 *  Vue ref() → React useState + localStorage sync.
 *  Vue useI18n → React useTranslation + i18n.changeLanguage.
 */
import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'

const themeNames = ['default', 'dusk', 'lime', 'ocean', 'retro', 'neo', 'forest', 'oscura']

export function usePreferences() {
  const { i18n } = useTranslation()
  const [currentTheme, setCurrentTheme] = useState(localStorage.getItem('tlo-theme-name') || 'default')
  const [isDark, setIsDark] = useState(localStorage.getItem('tlo-theme') === 'dark')
  const [lang, setLangState] = useState(localStorage.getItem('tlo-lang') || 'zh')

  const setTheme = useCallback((name: string) => {
    setCurrentTheme(name)
    document.documentElement.setAttribute('data-theme', name)
    if (name === 'oscura') {
      setIsDark(true)
      document.documentElement.classList.add('dark')
      localStorage.setItem('tlo-theme', 'dark')
    }
    localStorage.setItem('tlo-theme-name', name)
  }, [])

  const toggleDark = useCallback(() => {
    setIsDark(prev => {
      const next = !prev
      document.documentElement.classList.toggle('dark', next)
      localStorage.setItem('tlo-theme', next ? 'dark' : 'light')
      return next
    })
  }, [])

  const setLang = useCallback((l: string) => {
    setLangState(l)
    i18n.changeLanguage(l)
    localStorage.setItem('tlo-lang', l)
  }, [i18n])

  return { currentTheme, isDark, lang, themeNames, setTheme, toggleDark, setLang }
}
