import { expect, test, type Page } from '@playwright/test'

type Diagnostics = {
  consoleErrors: string[]
  pageErrors: string[]
  badResponses: string[]
  failedRequests: string[]
  activeView: string
}

const diagnostics = new WeakMap<Page, Diagnostics>()
const navItems = [
  '仪表盘', '工作流', '执行中心', '看板', '运行检查', '报告', '缺口发现',
  '记忆', '知识', '知识图谱', '产物', '智能对话', '可观测性', '运行历史',
]

function navButton(page: Page, name: string) {
  return page.getByRole('navigation').getByRole('button', { name, exact: true })
}

async function openDashboard(page: Page) {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Agent 注册表', exact: true })).toBeVisible()
}

test.beforeEach(async ({ page }) => {
  const state: Diagnostics = { consoleErrors: [], pageErrors: [], badResponses: [], failedRequests: [], activeView: '' }
  diagnostics.set(page, state)
  page.on('console', message => {
    if (message.type() === 'error') state.consoleErrors.push(`${message.text()} [view=${state.activeView} url=${message.location().url}]`)
  })
  page.on('pageerror', error => state.pageErrors.push(error.message))
  page.on('response', response => {
    if (response.status() >= 400) state.badResponses.push(`${response.status()} ${response.url()}`)
  })
  page.on('requestfailed', request => state.failedRequests.push(`${request.method()} ${request.url()} ${request.failure()?.errorText || ''}`))
})

test.afterEach(async ({ page }, testInfo) => {
  const state = diagnostics.get(page)
  if (!state) return
  const evidence = JSON.stringify(state, null, 2)
  if (state.consoleErrors.length || state.pageErrors.length || state.badResponses.length || state.failedRequests.length) {
    await testInfo.attach('browser-diagnostics.json', { body: Buffer.from(evidence), contentType: 'application/json' })
  }
  expect(
    state,
    `browser diagnostics: ${JSON.stringify(state)}`,
  ).toEqual({ consoleErrors: [], pageErrors: [], badResponses: [], failedRequests: [], activeView: expect.any(String) })
})

test.describe('Alice Studio real user paths', () => {
  test('dashboard renders backend-backed data', async ({ page }) => {
    await openDashboard(page)
    await expect(page.getByRole('heading', { name: '最近运行', exact: true })).toBeVisible()
    await expect(page.getByText(/Agent 注册表/).first()).toBeVisible()
  })

  test('every visible primary navigation item opens a non-blank view', async ({ page }) => {
    test.setTimeout(60_000)
    await openDashboard(page)
    for (const item of navItems) {
      diagnostics.get(page)!.activeView = item
      const button = navButton(page, item)
      await expect(button).toHaveCount(1)
      await button.click()
      await expect(page.locator('main')).toBeVisible()
      await page.waitForTimeout(100)
      expect((await page.locator('main').innerText()).trim().length).toBeGreaterThan(0)
    }
    const settings = page.getByRole('button', { name: '设置', exact: true })
    await expect(settings).toHaveCount(1)
    await settings.click()
    await expect(page.getByRole('heading', { name: '外观', exact: true })).toBeVisible()
  })

  test('legacy view routes are mounted by the current App router', async ({ page }) => {
    const legacyRoutes = [
      ['/#/settings', /外观|Appearance/],
      ['/#/projects/legacy/settings', /项目设置|Project Settings/],
      ['/#/projects/legacy/strategy', /策略规划|Strategy/],
      ['/#/projects/legacy/build', /Workflow Builder/],
      ['/#/registry', /注册中心|Registry/],
      ['/#/onboarding', /新建项目|New Project/],
    ] as const
    for (const [path, expected] of legacyRoutes) {
      diagnostics.get(page)!.activeView = path
      await page.goto(path)
      await expect(page.locator('body')).toContainText(expected)
    }
  })

  test('project selector switches context and validates onboarding input', async ({ page }) => {
    await openDashboard(page)
    const projectButton = page.getByRole('banner').getByRole('button').filter({ hasText: /BlueAlbum|ZJSN/ })
    await expect(projectButton).toHaveCount(1)
    await projectButton.click()
    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByRole('button', { name: '打开或接入项目', exact: true })).toBeVisible()
    await page.getByRole('button', { name: '打开或接入项目', exact: true }).click()
    const url = page.getByPlaceholder('https://your-test-app.com', { exact: true })
    await url.fill('bad')
    await page.getByRole('button', { name: '继续', exact: true }).click()
    await expect(page.getByText('请输入有效的 URL (以 https:// 开头)', { exact: true })).toBeVisible()
  })

  test('workflow form creates a draft and refreshes the list', async ({ page }) => {
    await openDashboard(page)
    await navButton(page, '工作流').click()
    const name = `e2e-playwright-${Date.now()}`
    await page.getByPlaceholder('工作流名称', { exact: true }).fill(name)
    await page.getByPlaceholder('描述这个工作流…', { exact: true }).fill('browser regression')
    await page.getByRole('button', { name: '保存草稿', exact: true }).click()
    await expect(page.getByText('已保存。', { exact: true })).toBeVisible()
    await expect(page.getByText(name, { exact: true })).toBeVisible()
  })

  test('workflow form publishes a workflow through the publish endpoint', async ({ page }) => {
    await openDashboard(page)
    await navButton(page, '工作流').click()
    const name = `e2e-published-${Date.now()}`
    await page.getByPlaceholder('工作流名称', { exact: true }).fill(name)
    await page.getByPlaceholder('描述这个工作流…', { exact: true }).fill('browser publish regression')
    await page.getByRole('button', { name: '发布', exact: true }).click()
    await expect(page.getByText('已保存。', { exact: true })).toBeVisible()
    const workflowRow = page.getByText(name, { exact: true }).locator('..')
    await expect(workflowRow).toContainText('Published')
  })

  test('workflow edit, inspect, replay and delete paths use backend contracts', async ({ page }) => {
    await openDashboard(page)
    await navButton(page, '工作流').click()
    const name = `e2e-crud-${Date.now()}`
    await page.getByPlaceholder('工作流名称', { exact: true }).fill(name)
    await page.getByPlaceholder('描述这个工作流…', { exact: true }).fill('before edit')
    await page.getByRole('button', { name: '保存草稿', exact: true }).click()
    await expect(page.getByText(name, { exact: true })).toBeVisible()

    await page.getByRole('button').filter({ hasText: name }).click()
    await page.getByPlaceholder('描述这个工作流…', { exact: true }).fill('after edit')
    const update = page.waitForResponse(response => response.url().includes('/api/v1/workflows/') && response.request().method() === 'PUT')
    await page.getByRole('button', { name: '保存草稿', exact: true }).click()
    await expect((await update).status()).toBe(200)
    await expect(page.getByText('已保存。', { exact: true })).toBeVisible()

    const inspect = page.waitForResponse(response => response.url().endsWith('/validate') && response.request().method() === 'POST')
    await page.getByRole('button', { name: '检查', exact: true }).click()
    await expect((await inspect).status()).toBe(200)
    await expect(page.getByRole('status')).toContainText(/校验未通过|Validation failed/)

    const replay = page.waitForResponse(response => response.url().endsWith('/api/v1/runs') && response.request().method() === 'POST')
    await page.getByRole('button', { name: '重放', exact: true }).click()
    await expect((await replay).status()).toBeLessThan(300)

    const remove = page.waitForResponse(response => response.url().includes('/api/v1/workflows/') && response.request().method() === 'DELETE')
    await page.getByRole('button', { name: '删除', exact: true }).click()
    await expect((await remove).status()).toBe(200)
  })

  test('run inspector artifact actions use mapped download and copy resources', async ({ page }) => {
    const workflowResponse = await page.request.post('http://127.0.0.1:8000/api/v1/workflows', {
      data: { name: `e2e-inspector-${Date.now()}`, description: 'inspector artifact test', version: '1.0.0', graph: { nodes: [], edges: [] }, status: 'draft' },
    })
    expect(workflowResponse.status()).toBe(200)
    const workflow = await workflowResponse.json()
    const runResponse = await page.request.post('http://127.0.0.1:8000/api/v1/runs', {
      data: { target: { type: 'workflow', id: workflow.workflow_id, version: 'latest' }, params: { input: {} }, execution: { mode: 'full', async_mode: false } },
    })
    expect(runResponse.status()).toBeLessThan(300)
    const runId = String((await runResponse.json()).run_id)
    const eventId = 'e2e-artifact-event'
    let inspectedRunId = runId
    await page.route('**/api/runs/*/inspector', async route => {
      inspectedRunId = route.request().url().split('/api/runs/')[1].split('/')[0]
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          header: { run_id: runId, status: 'completed', module: 'inspector-test', artifacts_count: 1 },
          summary: {}, timeline: [], agent_calls: [],
          artifacts: [{ event_id: eventId, path: 'reports/result.md', size: 12, download_url: `/api/runs/${inspectedRunId}/artifacts/${eventId}/download` }],
        }),
      })
    })
    await page.route(`**/api/runs/*/artifacts/${eventId}/download`, async route => {
      await route.fulfill({ status: 200, contentType: 'text/markdown', body: '# result' })
    })
    await openDashboard(page)
    await navButton(page, '运行检查').click()
    await page.locator('main').getByRole('button', { name: '产物', exact: true }).click()
    const downloadLink = page.locator('main').getByRole('link', { name: 'Download result.md', exact: true })
    await expect(downloadLink).toHaveAttribute('href', `/api/runs/${inspectedRunId}/artifacts/${eventId}/download`)
    const download = page.waitForEvent('download')
    await downloadLink.click()
    await expect((await download).suggestedFilename()).toBe('result.md')
    await page.context().grantPermissions(['clipboard-read', 'clipboard-write'], { origin: new URL(page.url()).origin })
    await page.locator('main').getByRole('button', { name: 'Copy result.md path', exact: true }).click()
    await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe('reports/result.md')
  })

  test('kanban add module, notification panel, agent actions and history pagination are interactive', async ({ page }) => {
    await page.route('**/api/v1/notifications*', async route => {
      if (route.request().method() !== 'GET') return route.continue()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ notifications: [{ id: 'bug:E2E-READ', kind: 'bug', severity: 'low', title: 'E2E notification', message: 'Read persistence check', read: false }], total: 1, unread: 1 }),
      })
    })
    await openDashboard(page)

    await page.getByTestId('notifications-button').click()
    await expect(page.getByTestId('notifications-panel')).toContainText('E2E notification')
    const notificationRead = page.waitForResponse(response => response.url().includes('/api/v1/notifications/') && response.url().includes('/read') && response.request().method() === 'PATCH')
    await page.getByTestId('notification-bug:E2E-READ').click()
    await expect((await notificationRead).status()).toBe(200)
    await expect(page.getByTestId('notification-bug:E2E-READ')).toHaveClass(/opacity-70/)

    await navButton(page, '看板').click()
    await page.getByTestId('kanban-add-module').click()
    const moduleName = `e2e-module-${Date.now()}`
    await page.getByLabel('Module name').fill(moduleName)
    const moduleCreate = page.waitForResponse(response => response.url().includes('/api/v1/modules') && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Create', exact: true }).click()
    await expect((await moduleCreate).status()).toBe(201)
    await expect(page.getByRole('status')).toContainText(/已保存|Created/)
    await page.getByRole('button', { name: 'Close', exact: true }).click()
    await expect(page.getByTestId(`kanban-module-${moduleName}`)).toBeVisible()
    await page.getByTestId(`kanban-module-${moduleName}`).click()
    await expect(page.getByRole('dialog', { name: `Manage pages for ${moduleName}` })).toBeVisible()
    await page.getByLabel('Page name').fill('login-page')
    await page.getByLabel('Description').fill('Login page configuration')
    await page.getByTestId('module-page-locators').fill('{invalid')
    await page.getByTestId('module-page-submit').click()
    await expect(page.getByRole('status')).toContainText('Locators must be valid JSON object')
    await page.getByTestId('module-page-url').fill('https://example.test/login')
     await page.getByTestId('module-page-locators').fill('{"username":"#username"}')
     await page.getByTestId('module-page-config').fill('{"requires_auth":true}')
     await page.getByTestId('module-page-execution').fill('{"wait_for":["username"],"actions":[{"action":"click","target":"submit"}]}')
    const pageCreate = page.waitForResponse(response => response.url().includes(`/api/v1/modules/${moduleName}/pages`) && response.request().method() === 'POST')
    await page.getByTestId('module-page-submit').click()
    await expect((await pageCreate).status()).toBe(201)
    await expect(page.getByTestId('module-page-login-page')).toContainText('Login page configuration')
     await expect(page.getByTestId('module-page-login-page')).toContainText('https://example.test/login')
     await page.getByRole('button', { name: 'Edit page login-page', exact: true }).click()
     await expect(page.getByTestId('module-page-execution')).toHaveValue(/wait_for/)
    await page.getByLabel('Page name').fill('login')
    await page.getByLabel('Description').fill('Login configuration')
    await page.getByTestId('module-page-url').fill('https://example.test/sign-in')
    await page.getByTestId('module-page-locators').fill('{"password":"#password"}')
    await page.getByTestId('module-page-config').fill('{"requires_auth":false}')
    await page.getByTestId('module-page-enabled').uncheck()
    const pageUpdate = page.waitForResponse(response => response.url().includes('/pages/login-page') && response.request().method() === 'PATCH')
    await page.getByTestId('module-page-submit').click()
    await expect((await pageUpdate).status()).toBe(200)
    await expect(page.getByTestId('module-page-login')).toContainText('Login configuration')
    await expect(page.getByTestId('module-page-login')).toContainText('https://example.test/sign-in')
    await expect(page.getByTestId('module-page-login')).toContainText('Disabled')
    page.once('dialog', dialog => dialog.accept())
    const pageDelete = page.waitForResponse(response => response.url().includes('/pages/login') && response.request().method() === 'DELETE')
    await page.getByRole('button', { name: 'Delete page login', exact: true }).click()
    await expect((await pageDelete).status()).toBe(200)
    await expect(page.getByTestId('module-pages-list')).not.toContainText('login')
    await page.getByRole('button', { name: 'Close', exact: true }).click()
    const renamedModule = `${moduleName}-renamed`
    await page.getByRole('button', { name: `Edit ${moduleName}`, exact: true }).click()
    await page.getByLabel('Module name').fill(renamedModule)
    const moduleUpdate = page.waitForResponse(response => response.url().includes(`/api/v1/modules/${moduleName}`) && response.request().method() === 'PATCH')
    await page.getByRole('button', { name: 'Save', exact: true }).click()
    await expect((await moduleUpdate).status()).toBe(200)
    await expect(page.getByRole('status')).toContainText(/已保存|Updated/)
    await page.getByRole('button', { name: 'Close', exact: true }).click()
    await expect(page.getByTestId(`kanban-module-${renamedModule}`)).toBeVisible()
    page.once('dialog', dialog => dialog.accept())
    const moduleDelete = page.waitForResponse(response => response.url().includes(`/api/v1/modules/${renamedModule}`) && response.request().method() === 'DELETE')
    await page.getByRole('button', { name: `Delete ${renamedModule}`, exact: true }).click()
    await expect((await moduleDelete).status()).toBe(200)

    await navButton(page, '仪表盘').click()
    const agentCard = page.getByRole('button').filter({ hasText: /已注册 Agent|Registered Agent/ }).first()
    await expect(agentCard).toBeVisible()
    await agentCard.click()
    const agentModes: string[] = []
    await page.route('**/api/v1/agents/run', async route => {
      agentModes.push(String((route.request().postDataJSON() as { mode?: string }).mode ?? ''))
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'queued', task_id: 'e2e-agent-task' }) })
    })
    const runAgent = page.getByTestId('agent-run')
    await runAgent.click()
    await expect(page.getByRole('status')).toContainText('e2e-agent-task')
    await page.getByTestId('agent-restart').click()
    await expect(page.getByRole('status')).toContainText('e2e-agent-task')
    expect(agentModes).toEqual(['full', 'resume'])
    await page.unroute('**/api/v1/agents/run')

    await page.route('**/api/v1/runs*', async route => {
      if (route.request().method() !== 'GET') return route.continue()
      const url = new URL(route.request().url())
      const offset = Number(url.searchParams.get('offset') ?? 0)
      const count = offset === 0 ? 10 : 1
      const runs = Array.from({ length: count }, (_, index) => ({
        run_id: `e2e-page-${offset + index}`,
        status: 'completed',
        module: 'history-test',
        created_at: new Date().toISOString(),
      }))
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ runs, total: 11 }) })
    })
    await navButton(page, '运行历史').click()
    const nextPage = page.getByRole('button', { name: /下一页|Next/ })
    await expect(nextPage).toBeEnabled()
    await nextPage.click()
    await expect(page.getByText('2', { exact: true })).toBeVisible()
    await expect(page.getByText('e2e-page-10', { exact: true })).toBeVisible()
    await page.unroute('**/api/v1/runs*')
    await page.unroute('**/api/v1/notifications*')
  })

  test('gap rescan and observability refresh reload backend snapshots', async ({ page }) => {
    await openDashboard(page)

    await navButton(page, '缺口发现').click()
    const rescan = page.getByRole('button', { name: '重新扫描', exact: true })
    await expect(rescan).toHaveCount(1)
    const gapRefresh = page.waitForResponse(response => response.url().includes('/api/v1/kpi/sop-status'))
    await rescan.click()
    await expect((await gapRefresh).status()).toBe(200)

    await navButton(page, '可观测性').click()
    const refresh = page.getByRole('button', { name: '刷新', exact: true })
    await expect(refresh).toHaveCount(1)
    const observabilityRefresh = page.waitForResponse(response => response.url().includes('/api/v1/observability/snapshot'))
    await refresh.click()
    await expect((await observabilityRefresh).status()).toBe(200)
  })

  test('gap lifecycle actions update non-empty backend data', async ({ page }) => {
    const seed = Date.now()
    const bugs = [
      { error_type: 'Missing Tests', status: 'fixed', action: '解决' },
      { error_type: 'Missing Types', status: 'wont_fix', action: '忽略' },
      { error_type: 'Flaky', status: 'closed', action: '归档' },
    ]
    const created: Array<{ bugId: string; status: string; action: string }> = []
    for (const bug of bugs) {
      const response = await page.request.post('http://127.0.0.1:8000/api/v1/bugs/add', {
        data: {
          module: `e2e-gap-${seed}`,
          page: `page-${seed}`,
          error_type: bug.error_type,
          root_cause: `e2e-gap-${seed}-${bug.status}`,
          severity: 'low',
          status: 'open',
        },
      })
      expect(response.status()).toBe(200)
      created.push({ bugId: String((await response.json()).bug_id), status: bug.status, action: bug.action })
    }

    await openDashboard(page)
    await navButton(page, '缺口发现').click()
    for (const bug of created) {
      const card = page.getByTestId(`gap-card-${bug.bugId}`)
      await expect(card).toBeVisible()
      const patchResponse = page.waitForResponse(response => response.url().endsWith(`/api/v1/bugs/${bug.bugId}`) && response.request().method() === 'PATCH')
      await card.getByRole('button', { name: bug.action, exact: true }).click()
      await expect((await patchResponse).status()).toBe(200)

      const listResponse = await page.request.get(`http://127.0.0.1:8000/api/v1/bugs/list?status=${bug.status}&limit=100`)
      expect(listResponse.status()).toBe(200)
      const list = await listResponse.json()
      expect(list.bugs.some((item: { bug_id?: string; id?: string; status?: string }) =>
        (item.bug_id ?? item.id) === bug.bugId && item.status === bug.status,
      )).toBe(true)
    }
  })

  test('reports export and settings controls work', async ({ page }) => {
    await openDashboard(page)
    await navButton(page, '报告').click()
    const exportButton = page.getByRole('button', { name: '导出', exact: true })
    await expect(exportButton).toHaveCount(1)
    const download = page.waitForEvent('download')
    await exportButton.click()
    await expect((await download).suggestedFilename()).toBe('alice-report.json')

    await page.getByRole('button', { name: '设置', exact: true }).click()
    const themeButton = page.getByRole('button', { name: 'Mahotsukai 午夜蓝', exact: true })
    await themeButton.click()
    const darkMode = page.getByRole('switch')
    await expect(darkMode).toHaveCount(1)
    await darkMode.click()
    await expect(darkMode).toHaveAttribute('aria-checked', 'false')
  })

  test('chat creates a session and can switch sessions without sending external data', async ({ page }) => {
    await openDashboard(page)
    await navButton(page, '智能对话').click()
    await page.getByRole('button', { name: '+ 新建对话', exact: true }).click()
    await expect(page.getByRole('button', { name: /New Chat 最近/ })).toBeVisible()
    await page.getByRole('button', { name: /New Chat 最近/ }).click()
    await expect(page.getByPlaceholder('询问 Alice 关于测试、覆盖率或 Agent 的问题…', { exact: true })).toBeVisible()
  })

  test('backend health and agent status return usable response shapes', async ({ page }) => {
    const health = await page.request.get('http://127.0.0.1:8000/health')
    expect(health.status()).toBe(200)
    expect((await health.json()).status).toBeDefined()
    const agents = await page.request.get('http://127.0.0.1:8000/api/v1/agents/status/all')
    expect(agents.status()).toBe(200)
    const body = await agents.json()
    expect(body).toHaveProperty('modules')
    expect(body).not.toHaveProperty('message', expect.stringContaining('governance.validator'))
  })
})
