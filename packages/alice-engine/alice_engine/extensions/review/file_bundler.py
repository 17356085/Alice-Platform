"""FileBundler — 关联文件打包分组。

借鉴 OCR 的智能文件打包理念:
  - 将关联文件合并为同一审查单元
  - 每个 bundle 作为独立审查上下文
  - 支持并发审查

分组规则:
  - Vue 组件: .vue + 同名 .ts/.css
  - i18n: 中英文 properties/json
  - 前后端配对: views/X.vue + api/X.py
  - 同目录同扩展名: 批量审查

用法:
    from alice_engine.extensions.review import FileBundler

    bundler = FileBundler()
    bundles = bundler.bundle(["src/views/Home.vue", "src/views/Home.ts", "src/api/user.py"])
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from pathlib import Path

from alice_engine.extensions.review.models import ReviewBundle

logger = logging.getLogger(__name__)


class FileBundler:
    """文件打包: 关联文件 → 审查单元。"""

    # Vue 组件配对: .vue + 同名 .ts/.js/.css/.scss
    _VUE_COMPANION = re.compile(r"^(.+)\.vue$")

    # i18n 配对: _zh.properties ↔ _en.properties
    _I18N_PAIR = re.compile(r"^(.+?)_(zh|en|ja|ko)\.(properties|json|yaml|yml)$")

    # 前后端配对: src/views/X/Y.vue ↔ src/api/X/Y.py
    _FRONTEND_PATH = re.compile(r"src/views?/(.+)\.(vue|tsx?)$")
    _BACKEND_PATH = re.compile(r"src/api/(.+)\.(py)$")

    def bundle(self, files: list[str]) -> list[ReviewBundle]:
        """将文件列表打包为审查单元。

        策略:
          1. 先尝试配对分组 (Vue组件、i18n、前后端)
          2. 剩余文件按同目录+同扩展名分组
          3. 仍然剩余的单独成组
        """
        if not files:
            return []

        remaining = set(files)
        bundles: list[ReviewBundle] = []

        # Pass 1: Vue 组件配对
        vue_bundles = self._bundle_vue_components(remaining)
        bundles.extend(vue_bundles)

        # Pass 2: i18n 配对
        i18n_bundles = self._bundle_i18n(remaining)
        bundles.extend(i18n_bundles)

        # Pass 3: 前后端配对
        fb_bundles = self._bundle_frontend_backend(remaining)
        bundles.extend(fb_bundles)

        # Pass 4: 同目录同扩展名分组
        dir_bundles = self._bundle_by_directory(remaining)
        bundles.extend(dir_bundles)

        return bundles

    def _bundle_vue_components(self, remaining: set[str]) -> list[ReviewBundle]:
        """Vue 组件配对: .vue + 同名 .ts/.js/.css/.scss。"""
        bundles = []
        vue_files = [f for f in remaining if f.endswith(".vue")]

        for vue_file in vue_files:
            base = self._VUE_COMPANION.match(vue_file)
            if not base:
                continue

            stem = base.group(1)
            companions = [vue_file]

            # 查找同名伴随文件
            for ext in (".ts", ".js", ".css", ".scss", ".less"):
                candidate = stem + ext
                if candidate in remaining and candidate != vue_file:
                    companions.append(candidate)

            if len(companions) > 1:
                bundle = ReviewBundle(
                    bundle_id=f"vue:{Path(stem).name}",
                    files=sorted(companions),
                    reason="Vue component pair",
                )
                bundles.append(bundle)
                for f in companions:
                    remaining.discard(f)

        return bundles

    def _bundle_i18n(self, remaining: set[str]) -> list[ReviewBundle]:
        """i18n 配对: 中英文 properties/json。"""
        bundles = []
        i18n_groups: dict[str, list[str]] = defaultdict(list)

        for f in list(remaining):
            match = self._I18N_PAIR.match(f)
            if match:
                stem = match.group(1)  # 去掉 _zh/_en 后缀
                i18n_groups[stem].append(f)

        for stem, group_files in i18n_groups.items():
            if len(group_files) > 1:
                bundle = ReviewBundle(
                    bundle_id=f"i18n:{Path(stem).name}",
                    files=sorted(group_files),
                    reason="i18n translation pair",
                )
                bundles.append(bundle)
                for f in group_files:
                    remaining.discard(f)

        return bundles

    def _bundle_frontend_backend(self, remaining: set[str]) -> list[ReviewBundle]:
        """前后端配对: views/X.vue ↔ api/X.py。"""
        bundles = []

        # 建立前端文件索引
        frontend_map: dict[str, str] = {}
        for f in list(remaining):
            match = self._FRONTEND_PATH.match(f)
            if match:
                key = match.group(1)  # 路径中间部分
                frontend_map[key] = f

        # 查找后端配对
        for f in list(remaining):
            match = self._BACKEND_PATH.match(f)
            if match:
                key = match.group(1)
                if key in frontend_map:
                    fe_file = frontend_map[key]
                    bundle = ReviewBundle(
                        bundle_id=f"fb:{Path(key).name}",
                        files=sorted([fe_file, f]),
                        reason="frontend-backend pair",
                    )
                    bundles.append(bundle)
                    remaining.discard(fe_file)
                    remaining.discard(f)

        return bundles

    def _bundle_by_directory(self, remaining: set[str]) -> list[ReviewBundle]:
        """同目录同扩展名分组。"""
        bundles = []
        dir_groups: dict[tuple[str, str], list[str]] = defaultdict(list)

        for f in remaining:
            path = Path(f)
            ext = path.suffix
            dir_key = str(path.parent)
            dir_groups[(dir_key, ext)].append(f)

        for (dir_path, ext), group_files in dir_groups.items():
            if len(group_files) >= 2:
                # 2+ 个同目录同扩展名文件 → 打包
                bundle = ReviewBundle(
                    bundle_id=f"dir:{Path(dir_path).name}/{ext}",
                    files=sorted(group_files),
                    reason=f"co-located {ext} files",
                )
                bundles.append(bundle)
                for f in group_files:
                    remaining.discard(f)
            else:
                # 单独文件 → 自成一组
                bundle = ReviewBundle(
                    bundle_id=f"single:{Path(group_files[0]).name}",
                    files=sorted(group_files),
                    reason="standalone file",
                )
                bundles.append(bundle)
                for f in group_files:
                    remaining.discard(f)

        return bundles
