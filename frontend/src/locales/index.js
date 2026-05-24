import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import en from './en'

const i18n = createI18n({
  legacy: true,
  locale: localStorage.getItem('rsod-locale') || 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages: { 'zh-CN': zhCN, en },
})

export default i18n
