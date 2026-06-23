"""
FileIndexer — scans project directory → indexes relevant files for discovery.

Builds a map of:
  - Router files (router/index.ts, router/index.js, src/router, etc.)
  - View/page components (src/views/, src/pages/, app/views/)
  - API files (src/api/, src/services/, src/utils/request.ts)
  - Menu/config files (menu config, sidebar config)
  - Store files (src/store/, src/stores/)

Output: FileIndex dataclass used by extractors.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from aitest.knowledge_model.schema import FrameworkType, FrameworkInfo

logger = logging.getLogger(__name__)


@dataclass
class FileIndex:
    """Indexed project files organized by category."""
    project_root: Path
    router_files: list[Path] = field(default_factory=list)
    view_files: list[Path] = field(default_factory=list)       # .vue, .tsx, .jsx
    component_files: list[Path] = field(default_factory=list)   # Shared components
    api_files: list[Path] = field(default_factory=list)         # API service files
    store_files: list[Path] = field(default_factory=list)       # State management
    menu_config_files: list[Path] = field(default_factory=list) # menu/sidebar config
    type_files: list[Path] = field(default_factory=list)        # .d.ts, types/
    config_files: list[Path] = field(default_factory=list)      # Other config
    tsconfig_path: Optional[Path] = None
    total_files: int = 0

    @property
    def has_router(self) -> bool:
        return len(self.router_files) > 0

    @property
    def view_count(self) -> int:
        return len(self.view_files)


class FileIndexer:
    """
    Scan project directory → categorized file index.

    Framework-aware: Vue projects scan for .vue + router/index.ts,
    React projects scan for .tsx + different router patterns.

    Usage:
        indexer = FileIndexer()
        index = indexer.scan("/path/to/project", framework_info)
        print(f"Found {index.view_count} views, {len(index.router_files)} router files")
    """

    # Common source directories (tried in order)
    SRC_DIRS = ["src", "app", "lib", "source"]

    # Router file patterns per framework
    ROUTER_PATTERNS = {
        FrameworkType.VUE_3: [
            "**/router/index.ts", "**/router/index.js",
            "**/router/routes.ts", "**/router/routes.js",
            "**/router/*.ts", "**/router/*.js",
            "src/router.ts", "src/router.js",
        ],
        FrameworkType.VUE_2: [
            "**/router/index.js", "**/router/index.ts",
            "src/router.js", "src/router.ts",
        ],
        FrameworkType.REACT: [
            "**/router/index.tsx", "**/router/index.jsx",
            "**/routes.tsx", "**/routes.ts",
            "src/App.tsx",  # Often contains routes inline
        ],
        FrameworkType.NEXT_JS: [
            "app/**/page.tsx", "app/**/page.jsx",  # File-based
            "src/app/**/page.tsx", "pages/**/*.tsx",
        ],
        FrameworkType.NUXT: [
            "pages/**/*.vue",  # File-based routing
            "app/**/*.vue",
        ],
    }

    # View file extensions per framework
    VIEW_EXTENSIONS = {
        FrameworkType.VUE_3: [".vue"],
        FrameworkType.VUE_2: [".vue"],
        FrameworkType.REACT: [".tsx", ".jsx"],
        FrameworkType.NEXT_JS: [".tsx", ".jsx"],
        FrameworkType.NUXT: [".vue"],
        FrameworkType.ANGULAR: [".component.ts"],
    }

    def scan(self, project_path: str | Path, framework: FrameworkInfo) -> FileIndex:
        """Scan project and return categorized file index."""
        root = Path(project_path).resolve()
        index = FileIndex(project_root=root, tsconfig_path=self._find_tsconfig(root))

        src_dir = self._find_src_dir(root)

        # Index router files
        index.router_files = self._find_router_files(root, src_dir, framework)

        # Index view files
        index.view_files = self._find_view_files(root, src_dir, framework)

        # Index component files
        index.component_files = self._find_component_files(root, src_dir, framework)

        # Index API files
        index.api_files = self._find_api_files(root, src_dir)

        # Index store files
        index.store_files = self._find_store_files(root, src_dir)

        # Index menu config
        index.menu_config_files = self._find_menu_configs(root, src_dir)

        # Index type files
        index.type_files = self._find_type_files(root, src_dir)

        # Count total
        index.total_files = (
            len(index.router_files) + len(index.view_files) +
            len(index.component_files) + len(index.api_files) +
            len(index.store_files) + len(index.menu_config_files)
        )

        logger.info(
            f"FileIndex scanned {root.name}: "
            f"{len(index.router_files)} router, {len(index.view_files)} views, "
            f"{len(index.api_files)} api, {len(index.store_files)} stores, "
            f"{len(index.menu_config_files)} menu configs"
        )
        return index

    # ── Internal ──────────────────────────────────────────────────────────

    def _find_src_dir(self, root: Path) -> Path:
        for d in self.SRC_DIRS:
            candidate = root / d
            if candidate.is_dir():
                return candidate
        return root

    def _find_tsconfig(self, root: Path) -> Optional[Path]:
        for name in ["tsconfig.json", "tsconfig.app.json", "jsconfig.json"]:
            p = root / name
            if p.exists():
                return p
        return None

    def _find_router_files(self, root: Path, src_dir: Path, fw: FrameworkInfo) -> list[Path]:
        patterns = self.ROUTER_PATTERNS.get(fw.framework, self.ROUTER_PATTERNS[FrameworkType.VUE_3])
        return self._glob_multi(root, patterns)

    def _find_view_files(self, root: Path, src_dir: Path, fw: FrameworkInfo) -> list[Path]:
        exts = self.VIEW_EXTENSIONS.get(fw.framework, [".vue"])
        # Search in common view directories
        view_dirs = ["src/views", "src/pages", "app/views", "app/pages",
                     "pages", "views", "src/screens"]
        result = []
        for vd in view_dirs:
            d = root / vd
            if d.is_dir():
                for ext in exts:
                    result.extend(d.rglob(f"*{ext}"))
        # If no view dirs found, search entire src
        if not result and src_dir != root:
            for ext in exts:
                result.extend(src_dir.rglob(f"*{ext}"))
                # Limit depth to avoid node_modules
                result = [p for p in result if "node_modules" not in str(p)]
        return sorted(set(result))

    def _find_component_files(self, root: Path, src_dir: Path, fw: FrameworkInfo) -> list[Path]:
        exts = self.VIEW_EXTENSIONS.get(fw.framework, [".vue"])
        comp_dirs = ["src/components", "src/shared/components",
                     "components", "app/components", "src/widgets"]
        result = []
        for cd in comp_dirs:
            d = root / cd
            if d.is_dir():
                for ext in exts:
                    result.extend(d.rglob(f"*{ext}"))
        return sorted(set(p for p in result if "node_modules" not in str(p)))

    def _find_api_files(self, root: Path, src_dir: Path) -> list[Path]:
        api_dirs = ["src/api", "src/services", "src/utils", "api", "services", "src/request"]
        patterns = ["**/*.ts", "**/*.js"]
        result = []
        for ad in api_dirs:
            d = root / ad
            if d.is_dir():
                for pat in patterns:
                    result.extend(d.rglob(pat))
        # Also find common request wrapper files
        for name in ["request.ts", "request.js", "http.ts", "http.js", "axios.ts", "fetch.ts"]:
            p = src_dir / name
            if p.exists():
                result.append(p)
        return sorted(set(p for p in result if "node_modules" not in str(p)))

    def _find_store_files(self, root: Path, src_dir: Path) -> list[Path]:
        store_dirs = ["src/store", "src/stores", "store", "stores", "src/state"]
        patterns = ["**/*.ts", "**/*.js"]
        result = []
        for sd in store_dirs:
            d = root / sd
            if d.is_dir():
                for pat in patterns:
                    result.extend(d.rglob(pat))
        return sorted(set(p for p in result if "node_modules" not in str(p)))

    def _find_menu_configs(self, root: Path, src_dir: Path) -> list[Path]:
        """Find menu/sidebar/navigation config files."""
        patterns = [
            "**/menu*.ts", "**/menu*.js", "**/sidebar*.ts", "**/sidebar*.js",
            "**/nav*.ts", "**/nav*.js", "**/navigation*.ts", "**/navigation*.js",
        ]
        result = []
        for pat in patterns:
            result.extend(src_dir.rglob(pat))
        return sorted(set(p for p in result if "node_modules" not in str(p)))

    def _find_type_files(self, root: Path, src_dir: Path) -> list[Path]:
        type_dirs = ["src/types", "src/typings", "types", "typings", "src/@types"]
        result = []
        for td in type_dirs:
            d = root / td
            if d.is_dir():
                result.extend(d.rglob("*.d.ts"))
                result.extend(d.rglob("*.ts"))
        return sorted(set(p for p in result if "node_modules" not in str(p)))

    @staticmethod
    def _glob_multi(root: Path, patterns: list[str]) -> list[Path]:
        result = []
        for pat in patterns:
            result.extend(root.glob(pat))
        return sorted(set(p for p in result if p.is_file()))
