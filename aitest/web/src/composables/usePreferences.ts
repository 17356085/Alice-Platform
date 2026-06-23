import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const currentTheme = ref(localStorage.getItem('tlo-theme-name') || 'default')
const isDark = ref(localStorage.getItem('tlo-theme') === 'dark')
const lang = ref(localStorage.getItem('tlo-lang') || 'zh')

const themeNames = ['default','dusk','lime','ocean','retro','neo','forest','oscura']

export function usePreferences() {
  const { locale } = useI18n()

  function setTheme(name: string) {
    currentTheme.value = name
    document.documentElement.setAttribute('data-theme', name)
    if (name === 'oscura') { isDark.value = true; document.documentElement.classList.add('dark'); localStorage.setItem('tlo-theme', 'dark') }
    localStorage.setItem('tlo-theme-name', name)
  }

  function toggleDark() {
    isDark.value = !isDark.value
    document.documentElement.classList.toggle('dark', isDark.value)
    localStorage.setItem('tlo-theme', isDark.value ? 'dark' : 'light')
  }

  function setLang(l: string) {
    lang.value = l
    locale.value = l
    localStorage.setItem('tlo-lang', l)
  }

  return { currentTheme, isDark, lang, themeNames, setTheme, toggleDark, setLang }
}
