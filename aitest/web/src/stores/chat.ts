import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  tools?: { name: string; input: string }[]
  suggestedTasks?: { title: string; description: string; category: string; complexity: string }[]
}

export interface ChatSession {
  id: string
  name: string
  messages: ChatMessage[]
  createdAt: string
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>(loadSessions())
  const activeId = ref(sessions.value[0]?.id || '')
  const streaming = ref(false)
  const streamContent = ref('')
  const currentTool = ref('')

  const activeSession = computed(() => sessions.value.find(s => s.id === activeId.value))
  const messages = computed(() => activeSession.value?.messages || [])

  function loadSessions(): ChatSession[] {
    try {
      return JSON.parse(localStorage.getItem('tlo-chat-sessions') || '[]')
    } catch { return [] }
  }
  function save() { localStorage.setItem('tlo-chat-sessions', JSON.stringify(sessions.value)) }

  function newSession() {
    const s: ChatSession = { id: Date.now().toString(36), name: 'New Chat', messages: [], createdAt: new Date().toISOString() }
    sessions.value.unshift(s)
    activeId.value = s.id
    save()
  }
  function deleteSession(id: string) {
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (activeId.value === id) activeId.value = sessions.value[0]?.id || ''
    save()
  }
  function renameSession(id: string, name: string) {
    const s = sessions.value.find(s => s.id === id)
    if (s) { s.name = name; save() }
  }

  function addMessage(role: 'user' | 'assistant', content: string, tools?: any[], tasks?: any[]) {
    if (!activeId.value) newSession()
    const s = sessions.value.find(s => s.id === activeId.value)
    if (s) {
      s.messages.push({ id: Date.now().toString(36), role, content, timestamp: new Date().toISOString(), tools, suggestedTasks: tasks })
      if (role === 'user' && s.messages.length === 1) s.name = content.slice(0, 40)
      save()
    }
  }

  // Simulated AI response (in production: WebSocket to backend AgentLoop)
  async function sendMessage(text: string) {
    addMessage('user', text)
    streaming.value = true
    streamContent.value = ''

    // Simulate tool usage
    const tools = simulateTools(text)
    for (const t of tools) {
      currentTool.value = t.name
      await new Promise(r => setTimeout(r, 400 + Math.random() * 600))
    }
    currentTool.value = ''

    // Simulate response
    const response = generateResponse(text)
    const tasks = generateTasks(text)
    for (let i = 0; i < response.length; i += 3) {
      streamContent.value = response.slice(0, i)
      await new Promise(r => setTimeout(r, 15))
    }
    streamContent.value = response
    await new Promise(r => setTimeout(r, 100))

    addMessage('assistant', response, tools, tasks)
    streaming.value = false
    streamContent.value = ''
  }

  return { sessions, activeId, activeSession, messages, streaming, streamContent, currentTool, newSession, deleteSession, renameSession, sendMessage }
})

// Simulated backend responses
function simulateTools(text: string) {
  const tools = []
  if (text.includes('覆盖') || text.includes('coverage')) tools.push({ name: 'Grep', input: 'searching TEST_CASES.md across 12 modules...' })
  if (text.includes('测试') || text.includes('test')) tools.push({ name: 'Glob', input: 'finding test_*.py in ZJSN_Test-master526/script/' })
  if (text.includes('bug') || text.includes('失败')) tools.push({ name: 'Read', input: 'reading trace_log.jsonl failure records...' })
  if (text.includes('模块') || text.includes('module')) tools.push({ name: 'Read', input: 'reading SOP_STATUS_*.json for 12 modules...' })
  return tools.slice(0, 3)
}

function generateResponse(text: string) {
  if (text.includes('覆盖') || text.includes('coverage'))
    return `## 测试覆盖分析\n\n基于 12 模块 1,082 测试用例分析：\n\n| 模块 | 页面数 | 阶段 | 评估 |\n|------|--------|------|------|\n| equipment | 4 | 9/9 | ✅ 完整 |\n| warehouse | 15 | 9/9 | ✅ 完整 |\n| personnel | 16 | 9/9 | ✅ 完整 |\n| system-management | 8 | 9/9 | ⚠️ 有问题 |\n| dcs | 5 | 9/9 | 📝 就绪 |\n\n**覆盖缺口**: equipment/camera 页面有 0 个测试用例。建议运行 Spec Pipeline。`
  if (text.includes('bug') || text.includes('失败') || text.includes('flaky'))
    return `## Flaky Test 分析\n\n最近 30 天执行统计：\n\n| 模块 | 失败率 | 主要根因 |\n|------|--------|---------|\n| warehouse | 35% | StaleLocator (60%), Timeout (25%) |\n| personnel | 18% | Data stale (70%), Assertion (20%) |\n| dcs | 12% | ServiceDown (80%) |\n\n**建议**: 对 warehouse 运行 QA Loop: \`aitest sop run --module=warehouse\``
  if (text.includes('安全') || text.includes('security'))
    return `## 安全测试覆盖\n\n当前安全测试状态：\n\n- ✅ Safety Auditor 已激活 (4 维检查)\n- ✅ 种子数据检测到 1 条 SENSITIVE_LEAK 违规\n- ❌ 无专门的 XSS/注入测试用例\n- ❌ 无权限绕过测试 (RBAC 之外)\n\n**建议**: 12 模块均需补充 Security 测试类型。`
  if (text.includes('模块') || text.includes('module'))
    return `## 模块状态总览\n\n12 模块，1,082 测试函数，39 个活跃 Skill。\n\n- **已完成**: equipment, lab, production, sales, system, system-role, tank, warehouse, workflow, personnel (10/12)\n- **待完成**: dcs (ready), system-management (completed_with_issues)\n\n**最薄弱点**: system-management - 8 页面但 81.1% pass rate。`
  return `## TLO Intelligence\n\n基于 5 个 ChromaDB collection (1,115 docs) 和 6,301 治理事件分析：\n\n- **RAG**: page_context(581) + tech_analysis(401) + page_objects(103) + known_issues(24) + project_context(6)\n- **30 天成本**: $50.80 (9 次审计)\n- **EventBus**: 6,301 事件\n\n可以问：测试覆盖 / Bug 趋势 / 安全分析 / 模块状态`
}

function generateTasks(text: string) {
  if (text.includes('覆盖') || text.includes('coverage')) {
    return [{ title: '补充 equipment/camera 测试', description: 'Spec Pipeline → 生成 camera 页面测试用例', category: 'test', complexity: 'medium' }]
  }
  if (text.includes('bug') || text.includes('失败')) {
    return [{ title: '修复 warehouse 不稳定测试', description: 'QA Loop auto-fix warehouse flaky tests', category: 'fix', complexity: 'high' }]
  }
  return []
}
