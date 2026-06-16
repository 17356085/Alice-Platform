# =============================================================================
# ZJSN Jenkins 镜像 — Python + Chrome + 测试依赖
# Selenium 4.44 自带 Selenium Manager，自动管理 ChromeDriver，无需手动安装
# =============================================================================

FROM jenkins/jenkins:lts-jdk17

USER root
ENV DEBIAN_FRONTEND=noninteractive

# ── 1. 切换阿里云源 ────────────────────────────────────────────────
RUN sed -i 's|http://deb.debian.org/debian|http://mirrors.aliyun.com/debian|g' /etc/apt/sources.list.d/debian.sources || true

# ── 2. 装 Python ──────────────────────────────────────────────────
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

# ── 3. 设置默认 python 命令 ───────────────────────────────────────
RUN python3 --version && update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# ── 4. 装 Chrome 系统依赖 + 浏览器 ────────────────────────────────
RUN apt-get update && apt-get install -y \
    wget curl \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 \
    libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 \
    libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 \
    fonts-liberation fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/* \
    && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && (dpkg -i /tmp/chrome.deb 2>/dev/null || (apt-get update && apt-get install -f -y)) \
    && rm -f /tmp/chrome.deb

# ── 5. 装 Python 依赖（Selenium Manager 自动管理 ChromeDriver）───
# 先装 apt 包避免 pandas 编译（省时间）
RUN apt-get update && apt-get install -y python3-pandas python3-yaml python3-dotenv || true \
    && rm -rf /var/lib/apt/lists/*
# 再用 pip 装测试框架（多源容错）
RUN pip install --no-cache-dir --default-timeout=120 --retries 5 \
    selenium \
    pytest \
    pytest-html \
    pytest-xdist \
    pytest-rerunfailures \
    allure-pytest \
    PyYAML \
    openpyxl \
    python-dotenv \
    -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn \
    || pip install --no-cache-dir --default-timeout=120 \
    selenium pytest pytest-html pytest-xdist pytest-rerunfailures \
    allure-pytest PyYAML openpyxl python-dotenv \
    || pip install --no-cache-dir \
    selenium pytest pytest-html pytest-xdist pytest-rerunfailures \
    allure-pytest PyYAML openpyxl python-dotenv

# ── 6. 验证 ──────────────────────────────────────────────────────
RUN echo "=== 验证 ===" \
    && python --version \
    && google-chrome --version \
    && python -c "import selenium,pytest,allure,dotenv; print('all ok')" \
    && echo "=== 环境就绪 ==="

USER jenkins
ENV HEADLESS=true ENV=test
