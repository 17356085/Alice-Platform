#!/usr/bin/env python
"""
API 测试模块初始化脚本

功能:
  1. 验证环境 + 依赖
  2. 生成测试数据（可选）
  3. 打印使用说明
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")
logger = logging.getLogger("api_init")


def check_environment():
    """检查必需环境变量。"""
    required = ["TEST_API_BASE_URL", "TEST_USER", "TEST_PASSWORD"]
    missing = [k for k in required if not os.getenv(k)]

    if missing:
        logger.warning(f"Missing env vars: {', '.join(missing)}")
        logger.info("Using defaults from conftest.py")
        return False
    return True


def check_dependencies():
    """检查必需包。"""
    try:
        import requests
        import pytest
        import allure
        logger.info(f"✓ requests {requests.__version__}")
        logger.info(f"✓ pytest {pytest.__version__}")
        logger.info(f"✓ allure-pytest")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False


def print_usage():
    """打印使用说明。"""
    print("""
================================================================================
                         API 测试模块 -- 快速开始
================================================================================

[结构]
  aitest/testing/api_client.py           # HTTP 通用驱动
  ZJSN_Test-master526/base/api_base.py   # 被测系统 API 基类
  ZJSN_Test-master526/script/*/test_api_*.py  # 模块测试用例

[环境配置] (.env 或系统环境变量)
  TEST_API_BASE_URL=https://...          # API 地址
  TEST_USER=admin                        # 用户名
  TEST_PASSWORD=password                 # 密码

[运行用例]
  # 单个模块
  pytest script/equipment/test_api_equipment.py -v

  # 全部 API 用例
  pytest script/*/test_api_*.py -v

  # 生成 Allure 报告
  pytest script/equipment/test_api_equipment.py -v --alluredir=allure-results
  allure serve allure-results

[文件说明]
  script/equipment/conftest.py           # 模块 fixture (登录 + 清理)
  script/equipment/test_api_equipment.py # equipment 模块 API 用例

[扩展新模块]
  1. 在 api_base.py 添加端点方法
  2. 在 script/<module>/test_api_<module>.py 编写用例
  3. 在 script/<module>/conftest.py 引入 api_client fixture

[调试]
  # 打印 API 请求/响应日志
  export PYTEST_ARGS="-v -s --log-cli-level=DEBUG"
  pytest script/equipment/test_api_equipment.py $PYTEST_ARGS

[文档]
  ZJSN_Test-master526/API_TESTING.md

================================================================================
""")


def main():
    """主入口。"""
    logger.info("Initializing API Testing Module...")

    if check_dependencies():
        logger.info("✓ All dependencies OK")
    else:
        sys.exit(1)

    if check_environment():
        logger.info("✓ Environment vars set")
    else:
        logger.info("  (using defaults from conftest.py)")

    print_usage()
    logger.info("Ready to run tests!")


if __name__ == "__main__":
    main()
