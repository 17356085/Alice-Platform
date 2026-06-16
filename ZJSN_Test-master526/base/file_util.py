"""文件工具 — 下载等待 & 验证

供测试用例中验证导出文件是否成功下载。
Chrome 下载通过 BaseDriver CDP 配置，driver 对象上挂载 .download_dir 属性。
"""
import glob
import logging
import os
import time

logger = logging.getLogger(__name__)


def wait_for_download(download_dir, timeout=30, file_pattern=None):
    """等待下载完成，返回第一个完成的文件路径或 None

    轮询下载目录，跳过 Chrome 临时文件 (.crdownload/.tmp)，
    等待文件大小稳定后返回路径。

    Args:
        download_dir: Chrome 下载目录绝对路径
        timeout: 最长等待秒数（默认 30）
        file_pattern: 可选 glob 模式过滤（如 "*.xlsx", "*.pdf"）

    Returns:
        str | None: 下载完成的文件完整路径，超时/失败返回 None
    """
    deadline = time.time() + timeout
    initial = set()
    try:
        initial = set(os.listdir(download_dir))
    except FileNotFoundError:
        logger.warning("下载目录不存在: %s", download_dir)
        return None

    while time.time() < deadline:
        try:
            current = set(os.listdir(download_dir))
        except FileNotFoundError:
            time.sleep(0.5)
            continue

        # 检测新出现的完整文件
        completed = [
            f for f in (current - initial)
            if not f.endswith('.crdownload')
            and not f.endswith('.tmp')
            and not os.path.isdir(os.path.join(download_dir, f))
        ]

        # 按模式过滤
        if file_pattern:
            matched = set(
                os.path.basename(p)
                for p in glob.glob(os.path.join(download_dir, file_pattern))
            )
            completed = [f for f in completed if f in matched]

        if completed:
            filepath = os.path.join(download_dir, completed[0])
            # 等待文件大小稳定（最多 10 次 × 0.3s = 3s）
            last_size = -1
            for _ in range(10):
                try:
                    cur = os.path.getsize(filepath)
                    if cur == last_size and cur > 0:
                        logger.info("下载完成: %s (%d bytes)", completed[0], cur)
                        return filepath
                    last_size = cur
                except OSError:
                    pass
                time.sleep(0.3)
            # 大小未稳定但文件存在 → 大概率完成
            logger.info("下载文件已检测（大小未稳定）: %s", completed[0])
            return filepath

        time.sleep(0.5)

    logger.warning("下载超时 (%ds): 未检测到新文件", timeout)
    return None
