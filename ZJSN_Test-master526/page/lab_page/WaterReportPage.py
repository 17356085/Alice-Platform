import time

# ====== 自检命令（逐一执行）======
# 1. ✅ class 是否继承 BasePage？
#    → grep -n "class \w\+Page:" → 必须是 "class WaterReportPage(BasePage):"
#
# 2. ✅ 无绝对 XPath？
#    → grep -n '//\*\[@id="app"\]' → 必须输出为空
#
# 3. ✅ 无 time.sleep？
#    → grep -n "time.sleep" → 必须为空（仅 TIMEOUT_CONFIG 常量除外）
#
# 4. ✅ 无 print()？
#    → grep -n "print(" → 必须输出为空
#
# 5. ✅ 有 navigate() 方法？
#    → grep -n "def navigate" → 必须命中