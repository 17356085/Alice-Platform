# =============================================================================
# ZJSN 自动化测试 — CI 执行环境镜像
# =============================================================================
# 用法:
#   docker build -t zjsn-test-runner:latest -f ci/Dockerfile .
#   docker run --rm \
#     -e BASE_URL=http://8.136.215.171:8081/ \
#     -e DEFAULT_USERNAME=admin \
#     -e DEFAULT_PASSWORD=xxx \
#     -e HEADLESS=true \
#     -v $(pwd)/allure-results:/app/allure-results \
#     -v $(pwd)/artifacts:/app/artifacts \
#     zjsn-test-runner:latest pytest -m smoke
# =============================================================================

FROM python:3.11-slim-bookworm

LABEL maintainer="ZJSN QA Team"
LABEL description="ZJSN UI 自动化测试执行环境 — Python 3.11 + Chrome + ChromeDriver"

# ── 环境变量 ────────────────────────────────────────────────────────
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    # Chrome 参数
    CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --headless=new"

# ── 安装 Chrome + 系统依赖 ─────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chrome 运行时依赖
    wget \
    curl \
    unzip \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libu2f-udev \
    libvulkan1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    # 调试工具
    vim \
    && rm -rf /var/lib/apt/lists/*

# ── 安装 Chrome 浏览器 ──────────────────────────────────────────────
RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i /tmp/chrome.deb || apt-get update && apt-get install -f -y \
    && rm -f /tmp/chrome.deb \
    && google-chrome --version

# ── 安装 ChromeDriver（版本匹配）────────────────────────────────────
# 从 Chrome 版本号提取主版本，拉取匹配的 ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+' | head -1) \
    && CHROME_MAJOR=$(echo "$CHROME_VERSION" | cut -d. -f1) \
    && echo "Chrome version: $CHROME_VERSION (major: $CHROME_MAJOR)" \
    && DRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" \
    && echo "Downloading ChromeDriver from: $DRIVER_URL" \
    && wget -q -O /tmp/chromedriver.zip "$DRIVER_URL" \
    && unzip -o /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64 \
    && chromedriver --version

# ── 应用目录 ────────────────────────────────────────────────────────
WORKDIR /app

# ── 先复制依赖文件（利用 Docker 缓存层） ──────────────────────────
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ── 复制项目源码 ──────────────────────────────────────────────────
COPY . .

# ── 创建输出目录 ──────────────────────────────────────────────────
RUN mkdir -p allure-results artifacts log

# ── 健康检查 ──────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import selenium; import pytest; import allure" || exit 1

# ── 默认命令 ──────────────────────────────────────────────────────
# 可通过 docker run 覆盖：
#   docker run zjsn-test-runner pytest -m smoke
#   docker run zjsn-test-runner pytest script/sales/
ENTRYPOINT ["python", "-m"]
CMD ["pytest", "-m", "smoke", "--alluredir=allure-results", "--tb=short", "-v"]
