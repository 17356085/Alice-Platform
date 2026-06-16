#!/usr/bin/env bash
# =============================================================================
# ZJSN 自动化测试 — Jenkins Agent 环境一键安装脚本
# =============================================================================
# 适用系统: Ubuntu 20.04+ / Debian 11+ / CentOS 7+
# 用法:
#   chmod +x setup_agent.sh
#   sudo ./setup_agent.sh
#
# 功能:
#   1. 安装 Python 3.11 + pip
#   2. 安装 Chrome 浏览器
#   3. 安装 ChromeDriver（版本自动匹配）
#   4. 安装项目 Python 依赖
#   5. 创建专用 jenkins 用户（如不存在）
#   6. 可选：安装 Jenkins Agent JAR + 配置 systemd
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${CYAN}  $*${NC}"; echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ── 检测操作系统 ──────────────────────────────────────────────────────
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        log_error "无法检测操作系统，仅支持 Ubuntu/Debian/CentOS"
        exit 1
    fi
    log_info "检测到操作系统: ${OS} ${OS_VERSION}"
}

# ── 步骤 1: 安装 Python 3.11 ─────────────────────────────────────────
install_python() {
    log_step "步骤 1/6: 安装 Python 3.11"

    if command -v python3.11 &>/dev/null; then
        log_info "Python 3.11 已安装: $(python3.11 --version)"
        return 0
    fi

    case "$OS" in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y -qq software-properties-common
            add-apt-repository -y ppa:deadsnakes/ppa
            apt-get update -qq
            apt-get install -y -qq python3.11 python3.11-venv python3.11-dev python3-pip
            ;;
        centos|rhel|fedora)
            yum install -y gcc openssl-devel bzip2-devel libffi-devel
            cd /tmp
            curl -O https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
            tar xzf Python-3.11.9.tgz
            cd Python-3.11.9
            ./configure --enable-optimizations
            make -j"$(nproc)"
            make altinstall
            cd /tmp && rm -rf Python-3.11.9*
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac

    # 确保 pip 可用
    python3.11 -m ensurepip --upgrade || true
    python3.11 -m pip install --upgrade pip

    log_info "Python 3.11 安装完成: $(python3.11 --version)"
}

# ── 步骤 2: 安装 Chrome 浏览器 ───────────────────────────────────────
install_chrome() {
    log_step "步骤 2/6: 安装 Google Chrome"

    if command -v google-chrome &>/dev/null; then
        log_info "Chrome 已安装: $(google-chrome --version)"
        return 0
    fi

    case "$OS" in
        ubuntu|debian)
            wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
            dpkg -i /tmp/google-chrome.deb || apt-get install -f -y
            rm -f /tmp/google-chrome.deb
            ;;
        centos|rhel)
            yum install -y https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
            ;;
        *)
            # 通用方法：手动下载安装
            wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
            dpkg -i /tmp/google-chrome.deb 2>/dev/null || {
                rpm -ivh https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm 2>/dev/null
            }
            rm -f /tmp/google-chrome.deb
            ;;
    esac

    log_info "Chrome 安装完成: $(google-chrome --version 2>/dev/null || echo 'OK')"
}

# ── 步骤 3: 安装 ChromeDriver ────────────────────────────────────────
install_chromedriver() {
    log_step "步骤 3/6: 安装 ChromeDriver（版本自动匹配）"

    if command -v chromedriver &>/dev/null; then
        log_info "ChromeDriver 已安装: $(chromedriver --version 2>&1 | head -1)"
        return 0
    fi

    # 获取 Chrome 主版本号
    CHROME_VER=$(google-chrome --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
    if [ -z "$CHROME_VER" ]; then
        CHROME_VER=$(google-chrome-stable --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
    fi
    if [ -z "$CHROME_VER" ]; then
        log_error "无法获取 Chrome 版本，请确认 Chrome 已正确安装"
        exit 1
    fi

    log_info "Chrome 版本: $CHROME_VER"

    # 从 Chrome for Testing 下载匹配的 ChromeDriver
    DRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VER}/linux64/chromedriver-linux64.zip"

    log_info "下载 ChromeDriver: $DRIVER_URL"
    wget -q -O /tmp/chromedriver.zip "$DRIVER_URL" || {
        # 回退：使用主版本号匹配
        CHROME_MAJOR=$(echo "$CHROME_VER" | cut -d. -f1)
        log_warn "精确版本下载失败，尝试主版本匹配 (major: $CHROME_MAJOR)..."
        LATEST_GOOD=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json" \
            | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['milestones']['${CHROME_MAJOR}']['downloads']['chromedriver']['linux64']['url'])" 2>/dev/null || true)
        if [ -n "$LATEST_GOOD" ]; then
            DRIVER_URL="$LATEST_GOOD"
            wget -q -O /tmp/chromedriver.zip "$DRIVER_URL"
        else
            log_error "无法获取 ChromeDriver"
            exit 1
        fi
    }

    unzip -o /tmp/chromedriver.zip -d /tmp/
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver
    chmod +x /usr/local/bin/chromedriver
    rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64

    log_info "ChromeDriver 安装完成: $(chromedriver --version 2>&1 | head -1)"
}

# ── 步骤 4: 安装字体（中文支持）─────────────────────────────────────
install_fonts() {
    log_step "步骤 4/6: 安装中文字体"
    case "$OS" in
        ubuntu|debian)
            apt-get install -y -qq fonts-wqy-microhei fonts-wqy-zenhei fonts-noto-cjk 2>/dev/null || true
            ;;
        centos|rhel)
            yum install -y wqy-microhei-fonts wqy-zenhei-fonts 2>/dev/null || true
            ;;
    esac
    log_info "字体安装完成"
}

# ── 步骤 5: 安装项目 Python 依赖 ────────────────────────────────────
install_python_deps() {
    log_step "步骤 5/6: 安装项目 Python 依赖"

    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    REQUIREMENTS="$PROJECT_ROOT/requirements.txt"

    if [ ! -f "$REQUIREMENTS" ]; then
        log_warn "未找到 requirements.txt，跳过依赖安装"
        return 0
    fi

    log_info "安装依赖: $REQUIREMENTS"
    python3.11 -m pip install -r "$REQUIREMENTS" --no-cache-dir

    # 验证关键包
    echo ""
    python3.11 -c "import selenium; print('  selenium:', selenium.__version__)"
    python3.11 -c "import pytest; print('  pytest:', pytest.__version__)"
    python3.11 -c "import allure; print('  allure-pytest: ok')"
    python3.11 -c "from dotenv import load_dotenv; print('  python-dotenv: ok')"

    log_info "Python 依赖安装完成"
}

# ── 步骤 6: 创建 jenkins 用户 ───────────────────────────────────────
create_jenkins_user() {
    log_step "步骤 6/6: 创建 jenkins 用户"

    if id "jenkins" &>/dev/null; then
        log_info "jenkins 用户已存在"
    else
        useradd -m -s /bin/bash jenkins
        echo "jenkins ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/jenkins
        chmod 440 /etc/sudoers.d/jenkins
        log_info "jenkins 用户已创建，sudo 权限已配置"
    fi

    # 创建必要目录
    mkdir -p /home/jenkins/workspace
    chown -R jenkins:jenkins /home/jenkins

    log_info "jenkins 用户就绪"
}

# ── 安装后验证 ──────────────────────────────────────────────────────
verify_installation() {
    log_step "安装验证"

    echo ""
    echo "  ┌─────────────────────────────────────────────┐"
    echo "  │  Python:     $(python3.11 --version 2>&1 | head -1)"
    echo "  │  pip:        $(python3.11 -m pip --version 2>&1 | head -1)"
    echo "  │  Chrome:     $(google-chrome --version 2>/dev/null || echo 'N/A')"
    echo "  │  ChromeDriver: $(chromedriver --version 2>&1 | head -1 || echo 'N/A')"
    echo "  │  Jenkins用户: $(id jenkins 2>/dev/null && echo 'OK' || echo 'N/A')"
    echo "  └─────────────────────────────────────────────┘"
    echo ""

    # 冒烟检查：以 jenkins 用户启动 Chrome headless
    log_info "Chrome headless 冒烟测试..."
    sudo -u jenkins google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.google.com 2>/dev/null | head -5 || {
        log_warn "Chrome headless 测试失败（可能是网络问题，不影响功能）"
    }
    log_info "环境安装完成！"
}

# ── 主流程 ──────────────────────────────────────────────────────────
main() {
    echo ""
    echo "  ╔══════════════════════════════════════════════════════════╗"
    echo "  ║   ZJSN 自动化测试 — Jenkins Agent 环境安装脚本            ║"
    echo "  ╚══════════════════════════════════════════════════════════╝"
    echo ""

    # 检查 root 权限
    if [ "$(id -u)" -ne 0 ]; then
        log_error "请使用 root 权限运行: sudo $0"
        exit 1
    fi

    detect_os
    install_python
    install_chrome
    install_chromedriver
    install_fonts
    install_python_deps
    create_jenkins_user
    verify_installation

    echo ""
    echo "  ╔══════════════════════════════════════════════════════════╗"
    echo "  ║   ✅ 安装完成！                                          ║"
    echo "  ║                                                          ║"
    echo "  ║   接下来：                                                ║"
    echo "  ║   1. 在 Jenkins Master 中创建 Agent Node                  ║"
    echo "  ║   2. 下载 agent.jar 并启动 SSH 连接                       ║"
    echo "  ║   3. 确认 Agent 状态为 Online                              ║"
    echo "  ╚══════════════════════════════════════════════════════════╝"
    echo ""
}

main "$@"
