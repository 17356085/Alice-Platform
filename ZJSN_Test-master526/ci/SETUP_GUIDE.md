# Jenkins CI/CD 部署配置指南 — ZJSN 自动化测试

> 版本：1.0 | 日期：2026-06-08
>
> 引用：[PROJECT_CONTEXT.md](../contexts/PROJECT_CONTEXT.md) | [AUTOMATION_ARCHITECTURE.md](../AUTOMATION_ARCHITECTURE.md)

---

## 目录

1. [架构概览](#1-架构概览)
2. [前置条件](#2-前置条件)
3. [快速开始（Docker Compose）](#3-快速开始docker-compose)
4. [传统部署（裸机 Jenkins）](#4-传统部署裸机-jenkins)
5. [Jenkins 插件安装](#5-jenkins-插件安装)
6. [Credentials 配置](#6-credentials-配置)
7. [创建 Pipeline Job](#7-创建-pipeline-job)
8. [Webhook 自动触发](#8-webhook-自动触发)
9. [通知配置](#9-通知配置)
10. [多环境管理](#10-多环境管理)
11. [常见问题排查](#11-常见问题排查)

---

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    Git 仓库 (Gitee/GitLab)                 │
│                  ZJSN_Test-master526                       │
└────────────────────┬────────────────────────────────────┘
                     │ ① Webhook / Polling
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Jenkins Master                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Pipeline (Jenkinsfile)                           │   │
│  │  Setup → Lint → Smoke → Regression → Report       │   │
│  └──────────────────────────────────────────────────┘   │
│  Credentials: URL / Username / Password / Webhook        │
│  Plugins: Allure / Pipeline / Git / Email Ext / ...      │
└────────────────────┬────────────────────────────────────┘
                     │ ② 分配任务
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Jenkins Agent                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Python 3.11 + Selenium + Chrome + ChromeDriver   │   │
│  │  pytest -m smoke --alluredir=allure-results        │   │
│  └──────────────────────────────────────────────────┘   │
│  运行环境: Docker Container / 裸机 Linux                    │
└─────────────────────────────────────────────────────────┘
                     │ ③ 产出
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Allure 报告 (Jenkins 内置)  +  失败截图 (Archive)        │
│  通知: 企业微信 Webhook / Email                            │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 前置条件

| 项目 | 最低要求 | 说明 |
|------|---------|------|
| **Jenkins** | 2.426+ (LTS) | 支持 JDK 17 |
| **Agent OS** | Ubuntu 20.04+ / Debian 11+ | 需能访问被测系统 `8.136.215.171:8081` |
| **Agent 内存** | ≥ 4 GB | Chrome headless 约消耗 500MB~1GB |
| **Agent 磁盘** | ≥ 20 GB | 含 Chrome + Python + 依赖 + 构建产物 |
| **Docker** | 24+ | （可选）使用 Docker 方式部署 |
| **Git** | 2.30+ | 拉取测试仓库 |

---

## 3. 快速开始（Docker Compose）

这是最快的方式，一键启动 Jenkins + Agent：

```bash
# 1. 进入 CI 目录
cd ZJSN_Test-master526/ci

# 2. 构建测试执行镜像（首次约 5~10 分钟）
docker compose build

# 3. 启动 Jenkins
docker compose up -d jenkins

# 4. 获取初始管理员密码
echo "等待 Jenkins 启动（约 30 秒）..."
sleep 30
docker compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# 5. 浏览器打开 http://localhost:8080
#    - 输入初始密码
#    - 选择 "安装推荐的插件"
#    - 创建管理员用户
```

**配置 Agent（Docker 方式）**：

```bash
# 1. 在 Jenkins UI 中创建 Agent Node:
#    Dashboard → Manage Jenkins → Nodes → New Node
#    - Name: zjsn-agent
#    - Type: Permanent Agent
#    - Remote root directory: /home/jenkins
#    - Labels: zjsn-test
#    - Usage: Only build jobs with label expressions matching this node
#    - Launch method: Launch agent via execution of command on the controller
#       或 Launch agent by connecting it to the controller

# 2. 获取 Secret:
#    在 Node 配置页面 → 保存 → 页面会显示 secret

# 3. 启动 Agent:
JENKINS_AGENT_SECRET=<your-secret> docker compose up -d jenkins-agent

# 4. 确认 Agent 状态为 Online
```

**仅运行测试（不启动 Jenkins）**：

```bash
docker compose --profile test-only run --rm test-runner pytest -m smoke
docker compose --profile test-only run --rm test-runner pytest script/sales/test_contract.py
```

---

## 4. 传统部署（裸机 Jenkins）

### 4.1 安装 Jenkins Master（Ubuntu）

```bash
# 添加 Jenkins 仓库
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null

# 安装 Jenkins + JDK 17
sudo apt-get update
sudo apt-get install -y fontconfig openjdk-17-jre jenkins

# 启动
sudo systemctl enable jenkins
sudo systemctl start jenkins

# 获取初始密码
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

### 4.2 配置 Agent 节点

在一台或多台 Linux 机器上执行：

```bash
# SSH 到 Agent 机器，执行环境安装脚本
scp ci/setup_agent.sh user@agent-host:/tmp/
ssh user@agent-host "sudo bash /tmp/setup_agent.sh"
```

然后在 Jenkins Master UI 中添加 Node：

1. **Dashboard** → **Manage Jenkins** → **Nodes** → **New Node**
2. 配置参数：

| 参数 | 值 |
|------|-----|
| Name | `zjsn-agent-01` |
| Type | Permanent Agent |
| Remote root directory | `/home/jenkins` |
| Labels | `zjsn-test linux chrome` |
| Usage | Only build jobs with label |
| Launch method | **Launch agent via SSH** |
| Host | Agent 机器的 IP |
| Credentials | 添加 jenkins 用户的 SSH 私钥 |
| Host Key Verification Strategy | Non verifying |

3. 保存后 Agent 自动连接，状态变为 **Online** ✅

---

## 5. Jenkins 插件安装

### 5.1 必需插件

在 **Dashboard → Manage Jenkins → Plugins → Available plugins** 中安装：

| 插件名称 | 用途 | 优先级 |
|----------|------|--------|
| **Pipeline** | Pipeline as Code 执行 | 🔴 必须 |
| **Pipeline: Stage View** | 流水线阶段可视化 | 🔴 必须 |
| **Git** | Git 仓库克隆 | 🔴 必须 |
| **Allure** | Allure 报告生成与展示 | 🔴 必须 |
| **Credentials Binding** | 安全注入凭据到环境变量 | 🔴 必须 |
| **Email Extension** | 邮件通知 | 🟠 高 |
| **Timestamper** | 控制台日志时间戳 | 🟡 中 |
| **Workspace Cleanup** | 构建后清理 | 🟡 中 |
| **Build Timeout** | 超时控制 | 🟡 中 |
| **AnsiColor** | 彩色控制台输出 | 🟢 低 |

### 5.2 Allure 插件配置

安装后需配置 Allure Commandline：

**Dashboard → Manage Jenkins → Tools → Allure Commandline installations**

```
Name: Allure
Install automatically: ✅
Version: 2.32.0（或最新稳定版）
```

### 5.3 插件一键安装（Jenkins CLI）

```bash
# 通过 jenkins-cli.jar 批量安装
java -jar jenkins-cli.jar -s http://localhost:8080/ -auth admin:token install-plugin \
  workflow-aggregator \
  pipeline-stage-view \
  git \
  allure-jenkins-plugin \
  credentials-binding \
  email-ext \
  timestamper \
  ws-cleanup \
  build-timeout \
  ansicolor
```

---

## 6. Credentials 配置

### 6.1 添加 Secret Text 凭据

**Dashboard → Manage Jenkins → Credentials → System → Global credentials → Add Credentials**

添加以下 3 个 Secret Text 凭据（Jenkinsfile 通过 `credentials()` 引用）：

| ID | 类型 | 值（示例） | 说明 |
|----|------|-----------|------|
| `zjsn-test-url` | Secret text | `http://8.136.215.171:8081` | 测试环境 URL |
| `zjsn-test-username` | Secret text | `admin` | 测试账号 |
| `zjsn-test-password` | Secret text | `********` | 测试密码 |

### 6.2 添加通知凭据（可选）

| ID | 类型 | 说明 |
|----|------|------|
| `wechat-webhook` | Secret text | 企业微信机器人 Webhook URL |
| `dingtalk-webhook` | Secret text | 钉钉机器人 Webhook URL |
| `smtp-credentials` | Username with password | SMTP 邮箱账号密码 |

### 6.3 添加 Git 凭据（如果仓库为私有）

| 类型 | 说明 |
|------|------|
| SSH Username with private key | Git SSH 私钥（推荐） |
| Username with password | Git HTTP 账号密码/Token |

### 6.4 Jenkinsfile 中 Credentials 的对应关系

```groovy
environment {
    // 这些 ID 必须与上面创建的 Credential ID 完全一致
    BASE_URL         = credentials('zjsn-test-url')
    DEFAULT_USERNAME = credentials('zjsn-test-username')
    DEFAULT_PASSWORD = credentials('zjsn-test-password')
}
```

---

## 7. 创建 Pipeline Job

### 7.1 新建 Pipeline 项目

1. **Dashboard** → **New Item**
2. 输入名称 `ZJSN_Test`
3. 选择 **Pipeline**
4. 点击 **OK**

### 7.2 配置 Pipeline

**General** 标签：

| 参数 | 值 |
|------|-----|
| Discard old builds | Strategy: Log Rotation, Max builds: 30 |
| GitHub project | （可选）仓库 URL |
| This project is parameterized | ✅（参数已在 Jenkinsfile 中定义） |

**Pipeline** 标签：

| 参数 | 值 |
|------|-----|
| Definition | Pipeline script from SCM |
| SCM | Git |
| Repository URL | `git@xxx:ZJSN_Test-master526.git`（或 HTTP URL） |
| Credentials | 选择上面创建的 Git 凭据 |
| Branch Specifier | `*/main`（或 `*/master`） |
| Script Path | `Jenkinsfile` |
| Lightweight checkout | ✅ |

**保存**。

### 7.3 首次构建

点击 **Build with Parameters** → 选择 `TARGET_ENV=test` → **Build**

首次构建会：
1. 拉取仓库代码
2. 安装 Python + Chrome + ChromeDriver
3. 执行冒烟测试
4. 生成 Allure 报告

### 7.4 流水线触发策略

| 触发方式 | 配置 | 适用场景 |
|---------|------|---------|
| **手动触发** | Build with Parameters | 日常按需执行 |
| **定时触发** | Build periodically: `H 8 * * 1-5` | 工作日每天 8 点自动跑冒烟 |
| **Push 触发** | Webhook（见下一节） | 代码提交自动触发 |
| **定时全量** | Build periodically: `H 2 * * 0` + RUN_REGRESSION=true | 每周日凌晨 2 点全量回归 |

---

## 8. Webhook 自动触发

### 8.1 Gitee（码云）

1. 安装 **Gitee Plugin**
2. Gitee 仓库 → **管理** → **WebHooks** → **添加 webHook**
3. URL: `http://<jenkins-server>:8080/gitee-project/ZJSN_Test`
4. 事件：Push / Tag Push
5. 密码：自定义（与 Jenkins 中 Gitee 配置一致）

### 8.2 GitLab

1. GitLab 仓库 → **Settings** → **Webhooks**
2. URL: `http://<jenkins-server>:8080/project/ZJSN_Test`
3. Trigger: Push events
4. Secret token: 自定义（Jenkins Job 中配置）

### 8.3 Generic Webhook

使用 **Generic Webhook Trigger** 插件：

```groovy
triggers {
    GenericTrigger(
        genericVariables: [
            [key: 'ref', value: '$.ref']
        ],
        causeString: 'Triggered on $ref',
        token: 'zjsn-test-trigger',
        printContributedVariables: true,
        printPostContent: true
    )
}
```

---

## 9. 通知配置

### 9.1 企业微信通知

在 Jenkinsfile 中已内置企业微信 Webhook 通知，只需在 Jenkins 中配置环境变量：

**Dashboard → Manage Jenkins → Configure System → Global properties**

添加环境变量：

```
Name:  WECHAT_WEBHOOK_URL
Value: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx
```

### 9.2 邮件通知

1. **Manage Jenkins → Configure System → Extended E-mail Notification**

```
SMTP server: smtp.example.com
SMTP Port: 465
Use SSL: ✅
Credentials: （选择 smtp-credentials）
Default Recipients: qa-team@your-company.com
```

2. 或在 Jenkinsfile 中通过环境变量覆盖收件人：

```
Name:  NOTIFY_EMAIL
Value: qa-team@your-company.com
```

### 9.3 钉钉通知

安装 **DingTalk** 插件后，在 Jenkinsfile 的 `post` 块中添加：

```groovy
dingtalk(
    robot: 'zjsn-qa-robot',
    type: 'MARKDOWN',
    title: 'ZJSN 测试结果',
    text: [
        "## ${currentBuild.result}",
        "- Job: ${env.JOB_NAME}",
        "- Build: [#${env.BUILD_NUMBER}](${env.BUILD_URL})",
        "- Allure: [查看报告](${env.BUILD_URL}allure)"
    ]
)
```

---

## 10. 多环境管理

### 10.1 环境配置文件

项目 `config/` 目录已支持 3 套环境，通过 `ENV` 变量切换：

| ENV 值 | 配置文件 | 适用场景 |
|--------|---------|---------|
| `dev` | `config/dev.py` | 开发联调环境 |
| `test` | `config/test.py` | 测试环境（默认） |
| `staging` | `config/staging.py` | 预发布/灰度环境 |

### 10.2 Jenkins 中创建多环境 Job

**方案 A：参数化（推荐）**

Jenkinsfile 已内置 `TARGET_ENV` 参数，构建时手动选择。

**方案 B：多个 Job**

```
ZJSN_Test_DEV      → TARGET_ENV=dev, 每天 8 点
ZJSN_Test_TEST     → TARGET_ENV=test, 每天 8 点
ZJSN_Test_STAGING  → TARGET_ENV=staging, 每周末
```

### 10.3 按环境配置 Credentials

不同环境可创建不同的 Credential：

```
zjsn-dev-url      → http://dev-server:8081/
zjsn-test-url     → http://8.136.215.171:8081/
zjsn-staging-url  → http://staging-server:8081/
```

在 Jenkinsfile 中按环境引用：

```groovy
environment {
    BASE_URL = credentials("zjsn-${params.TARGET_ENV}-url")
}
```

---

## 11. 常见问题排查

### 11.1 Agent 连接失败

**现象**：Agent 状态为 `Offline`，日志显示 `Connection refused`

**排查**：

```bash
# 检查 Agent 机器网络
ping <jenkins-master-ip>

# 检查 50000 端口
nc -zv <jenkins-master-ip> 50000

# 检查 agent.jar 进程
ps aux | grep agent.jar

# 查看 Agent 日志
tail -f /home/jenkins/remoting/logs/*.log
```

### 11.2 Chrome 启动失败

**现象**：`selenium.common.exceptions.WebDriverException: unknown error: Chrome failed to start`

**排查**：

```bash
# 确认 Chrome 可执行
google-chrome --version

# 测试 headless 模式
google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.baidu.com

# 检查 sandbox（Docker 必须加 --no-sandbox）
# 确认 Jenkinsfile 中 HEADLESS=true 已设置

# 检查 /dev/shm 大小（Docker 默认 64MB，Chrome 需要更多）
df -h /dev/shm
# 解决方案：docker run --shm-size=2g 或加 --disable-dev-shm-usage
```

### 11.3 ChromeDriver 版本不匹配

**现象**：`This version of ChromeDriver only supports Chrome version XXX`

**排查**：

```bash
# 查看版本
google-chrome --version
chromedriver --version

# 重新安装匹配的 ChromeDriver
# 或使用 Dockerfile（已内置版本匹配逻辑）
```

### 11.4 Allure 报告为空

**现象**：Allure 报告页面显示 "No data to display"

**排查**：

```bash
# 确认 allure-results 目录存在且非空
ls -la allure-results/

# 确认 pytest 使用了 --alluredir 参数
# 确认 Allure 插件配置正确（Manage Jenkins → Tools）
```

### 11.5 测试连接被测系统超时

**现象**：测试报 `TimeoutException`，页面无法打开

**排查**：

```bash
# 从 Agent 机器测试网络连通性
curl -v http://8.136.215.171:8081/

# 检查防火墙规则
# 确认 BASE_URL credential 的值正确
```

### 11.6 构建超时被 Kill

**现象**：流水线在 2 小时后被强制终止

**解决方案**：

修改 Jenkinsfile 中 `options.timeout`：
```groovy
options {
    timeout(time: 4, unit: 'HOURS')  // 增加至 4 小时
}
```

或通过构建参数覆盖。

---

## 附录 A: 文件清单

```
ZJSN_Test-master526/
├── Jenkinsfile                  # 流水线定义（核心文件）
├── ci/
│   ├── Dockerfile               # CI 执行环境镜像
│   ├── docker-compose.yml       # Jenkins + Agent 本地部署
│   ├── setup_agent.sh           # Agent 环境一键安装脚本
│   └── SETUP_GUIDE.md           # 本文件
├── requirements.txt             # Python 依赖锁定
├── pytest.ini                   # pytest 配置（markers/插件）
├── config/                      # 环境配置（dev/test/staging）
│   ├── __init__.py              #   配置入口 + 环境选择
│   ├── base.py                  #   公共配置
│   ├── dev.py                   #   开发环境
│   ├── test.py                  #   测试环境
│   └── staging.py               #   预发布环境
└── .env.example                 # 环境变量模板
```

## 附录 B: 快速操作速查表

| 操作 | 命令/位置 |
|------|----------|
| 构建冒烟测试 | `Jenkins → ZJSN_Test → Build with Parameters → TARGET_ENV=test` |
| 构建全量回归 | `Jenkins → ZJSN_Test → Build with Parameters → 勾选 RUN_REGRESSION` |
| 指定模块测试 | `Build with Parameters → TEST_PATH=script/sales/test_contract.py` |
| 查看 Allure 报告 | 构建页面 → 左侧菜单 **Allure Report** |
| 下载失败截图 | 构建页面 → **Artifacts** → artifacts/failures/ |
| Docker 启动 Jenkins | `docker compose -f ci/docker-compose.yml up -d jenkins` |
| Docker 仅跑测试 | `docker compose -f ci/docker-compose.yml --profile test-only run test-runner pytest -m smoke` |
| Agent 环境安装 | `sudo bash ci/setup_agent.sh` |
| 重启 Jenkins | `sudo systemctl restart jenkins` |
| 查看 Jenkins 日志 | `docker compose logs -f jenkins` 或 `sudo journalctl -u jenkins -f` |

---

*文档维护：CI/CD 架构变更后同步更新本文件*
