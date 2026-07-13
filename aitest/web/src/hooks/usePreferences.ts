/** Theme/language preferences hook — React port.
 *  Vue ref() → React useState + localStorage sync.
 *  Vue useI18n → React useTranslation + i18n.changeLanguage.
 */
import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'

const themeNames = ['mahotsukai', 'alice', 'aoko', 'soujuurou']

export function usePreferences() {
  const { i18n } = useTranslation()
  const storedTheme = localStorage.getItem('tlo-theme-name') || 'mahotsukai'
  // Backward compat: the former default/Alice palette is now Mahotsukai.
  const initialTheme = storedTheme === 'default' ? 'mahotsukai' : storedTheme
  const [currentTheme, setCurrentTheme] = useState(initialTheme)
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
