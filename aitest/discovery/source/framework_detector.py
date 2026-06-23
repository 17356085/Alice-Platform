"""
TechStackDetector — unified frontend + backend tech stack detection.

Frontend: package.json → Vue/React/Angular/Next/Nuxt
Backend:  pom.xml / build.gradle / requirements.txt → Spring Boot / Flask / FastAPI / Gin
Output:   TechStack dataclass (frontend + backends)
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from aitest.knowledge_model.schema import (
    FrameworkType, FrameworkInfo,
    BackendFramework, BackendLanguage, BuildSystem, BackendInfo,
)

logger = logging.getLogger(__name__)

# ── Framework signatures ──────────────────────────────────────────────────

FRAMEWORK_SIGNATURES = {
    FrameworkType.VUE_3: {
        "dependencies": ["vue"],
        "version_hint": "^3.",
        "router": "vue-router",
        "state": ["pinia"],
        "build": ["vite", "@vue/cli-service"],
    },
    FrameworkType.VUE_2: {
        "dependencies": ["vue"],
        "version_hint": "^2.",
        "router": "vue-router",
        "state": ["vuex"],
        "build": ["@vue/cli-service", "webpack"],
    },
    FrameworkType.REACT: {
        "dependencies": ["react", "react-dom"],
        "version_hint": "^18|^19",
        "router": ["react-router-dom"],
        "state": ["redux", "zustand", "jotai", "recoil"],
        "build": ["react-scripts", "vite", "webpack"],
    },
    FrameworkType.NEXT_JS: {
        "dependencies": ["next"],
        "version_hint": "^13|^14|^15",
        "router": "next/router",  # built-in
        "state": [],
        "build": [],  # built-in
    },
    FrameworkType.NUXT: {
        "dependencies": ["nuxt"],
        "version_hint": "^3.",
        "router": "",  # built-in file-based
        "state": [],
        "build": [],
    },
    FrameworkType.ANGULAR: {
        "dependencies": ["@angular/core"],
        "version_hint": "^17|^18|^19",
        "router": ["@angular/router"],
        "state": ["@ngrx/store"],
        "build": ["@angular/cli"],
    },
}

# Known UI libraries
UI_LIBRARY_SIGNATURES = {
    "element-plus": ["element-plus"],
    "element-ui": ["element-ui"],
    "ant-design-vue": ["ant-design-vue"],
    "antd": ["antd"],
    "naive-ui": ["naive-ui"],
    "vuetify": ["vuetify"],
    "primevue": ["primevue"],
    "mui": ["@mui/material", "@mui/joy"],
    "shadcn-vue": ["radix-vue"],
    "shadcn-ui": ["@radix-ui/react-*"],
    "arco-design": ["@arco-design/web-vue"],
    "tdesign": ["tdesign-vue-next", "tdesign-react"],
}

# Known HTTP clients
HTTP_CLIENT_SIGNATURES = ["axios", "@tanstack/react-query", "umi-request", "@vueuse/core"]


class FrameworkDetector:
    """
    Detect framework from package.json.

    Usage:
        detector = FrameworkDetector()
        info = detector.detect("/path/to/project")
        # FrameworkInfo(framework=VUE_3, version="3.4", router_package="vue-router", ...)
    """

    @staticmethod
    def find_package_json(project_path: str | Path) -> Optional[Path]:
        """Find package.json at root or in 1-level subdirectories.

        Multi-module projects (e.g., Java backend + Vue frontend) often have
        package.json in a subdirectory like ``front/``.  Return the path to
        the file itself (not the containing directory).
        """
        root = Path(project_path)
        direct = root / "package.json"
        if direct.exists():
            return direct
        try:
            for d in sorted(root.iterdir()):
                if d.is_dir() and not d.name.startswith('.') and d.name != 'node_modules':
                    candidate = d / "package.json"
                    if candidate.exists():
                        return candidate
        except (PermissionError, OSError):
            pass
        return None

    def detect(self, project_path: str | Path) -> Optional[FrameworkInfo]:
        """Detect framework from project root (or 1-level subdirectory).

        Returns None if no package.json found at either location.
        """
        root = Path(project_path)
        pkg_path = self.find_package_json(root)
        if pkg_path is None:
            logger.warning(f"No package.json found at {root} (root or 1-level subdirs)")
            return None

        # project_root is the directory containing the actual package.json
        actual_root = pkg_path.parent

        pkg = self._read_json(pkg_path)
        if not pkg:
            return None

        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        dep_names = set(deps.keys())

        # Detect framework
        framework = self._detect_framework(dep_names, deps)
        if framework == FrameworkType.UNKNOWN:
            logger.info(f"Unknown framework in {actual_root}, deps: {sorted(dep_names)[:20]}")

        # Detect UI library
        ui_library = self._detect_ui_library(dep_names)

        # Detect build tool
        build_tool = self._detect_build_tool(dep_names, actual_root)

        # Detect router
        router_package = self._detect_router(framework, dep_names)

        # Detect state management
        state_mgmt = self._detect_state_mgmt(framework, dep_names)

        # Detect HTTP client
        http_client = self._detect_http_client(dep_names)

        # Check TypeScript
        has_ts = (actual_root / "tsconfig.json").exists()

        # Get version
        version = self._get_version(framework, deps)

        return FrameworkInfo(
            framework=framework,
            version=version,
            router_package=router_package,
            ui_library=ui_library,
            build_tool=build_tool,
            state_management=state_mgmt,
            http_client=http_client,
            typescript=has_ts,
            project_root=str(actual_root.resolve()),
        )

    # ── Internal detection methods ───────────────────────────────────────

    def _detect_framework(self, dep_names: set, deps: dict) -> FrameworkType:
        for fw, sig in FRAMEWORK_SIGNATURES.items():
            required = set(sig["dependencies"])
            if required.issubset(dep_names):
                # Check version hint
                for dep in required:
                    ver = deps.get(dep, "")
                    if sig["version_hint"] and ver:
                        import re
                        if re.search(sig["version_hint"], ver):
                            return fw
                # Version hint not matched but dep exists — still a match
                return fw
        return FrameworkType.UNKNOWN

    def _detect_ui_library(self, dep_names: set) -> str:
        for name, packages in UI_LIBRARY_SIGNATURES.items():
            if any(p in dep_names for p in packages):
                return name
        return ""

    def _detect_build_tool(self, dep_names: set, root: Path) -> str:
        # Check package.json scripts
        pkg = self._read_json(root / "package.json")
        scripts = pkg.get("scripts", {}) if pkg else {}
        for name in scripts:
            if "vite" in name or "vite" in str(scripts.get(name, "")):
                return "vite"
            if "webpack" in str(scripts.get(name, "")):
                return "webpack"
        # Check dependencies
        if "vite" in dep_names:
            return "vite"
        if "webpack" in dep_names or "@vue/cli-service" in dep_names:
            return "webpack"
        if "turbo" in dep_names:
            return "turbo"
        # Check for config files
        if (root / "vite.config.ts").exists() or (root / "vite.config.js").exists():
            return "vite"
        if (root / "webpack.config.js").exists():
            return "webpack"
        return ""

    def _detect_router(self, framework: FrameworkType, dep_names: set) -> str:
        sig = FRAMEWORK_SIGNATURES.get(framework, {})
        router = sig.get("router", "")
        if isinstance(router, list):
            for r in router:
                if r in dep_names:
                    return r
        elif router and router in dep_names:
            return router
        return router if isinstance(router, str) else ""

    def _detect_state_mgmt(self, framework: FrameworkType, dep_names: set) -> str:
        sig = FRAMEWORK_SIGNATURES.get(framework, {})
        candidates = sig.get("state", [])
        for s in candidates:
            if s in dep_names:
                return s
        return ""

    def _detect_http_client(self, dep_names: set) -> str:
        for client in HTTP_CLIENT_SIGNATURES:
            if client in dep_names:
                return client
        return ""

    def _get_version(self, framework: FrameworkType, deps: dict) -> str:
        sig = FRAMEWORK_SIGNATURES.get(framework, {})
        for dep in sig.get("dependencies", []):
            ver = deps.get(dep, "")
            if ver:
                return ver.lstrip("^~>= ")
        return ""

    @staticmethod
    def _read_json(path: Path) -> Optional[dict]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read {path}: {e}")
            return None


# ══════════════════════════════════════════════════════════════════════════
#  TechStackDetector — unified frontend + backend
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class TechStack:
    """Complete tech stack for a project — frontend + backend(s)."""
    project_path: str = ""
    frontend: Optional[FrameworkInfo] = None
    backends: list[BackendInfo] = field(default_factory=list)

    @property
    def has_frontend(self) -> bool:
        return self.frontend is not None and self.frontend.framework != FrameworkType.UNKNOWN

    @property
    def has_backend(self) -> bool:
        return len(self.backends) > 0

    @property
    def backend_summary(self) -> dict:
        """Aggregated backend info for API responses.

        Prioritizes: real frameworks over UNKNOWN, production DBs over test DBs,
        majority language/build-system.
        """
        if not self.backends:
            return {}

        # Helper: pick most frequent from a list
        def _top(items: list) -> str:
            if not items:
                return ""
            counts: dict[str, int] = {}
            for i in items:
                counts[i] = counts.get(i, 0) + 1
            return max(counts, key=counts.get)

        # Exclude parent-POM-only entries for counting
        real = [b for b in self.backends if not b.parent_pom] or self.backends

        frameworks = [b.framework.value for b in real if b.framework != BackendFramework.UNKNOWN]
        languages = [b.language.value for b in real if b.language != BackendLanguage.UNKNOWN]
        versions = [b.language_version for b in real if b.language_version]
        build_systems = [b.build_system.value for b in real if b.build_system != BuildSystem.UNKNOWN]
        services = [b.service_name for b in real if b.service_name]
        db_types = [b.db_type for b in real if b.db_type and b.db_type != "h2"]  # prefer prod DB
        if not db_types:
            db_types = [b.db_type for b in real if b.db_type]  # fallback: include h2
        orms = [b.orm for b in real if b.orm]

        return {
            "framework": _top(frameworks),
            "frameworks": list({} | {f: None for f in frameworks}),  # dedup preserving order
            "language": _top(languages),
            "languages": list({} | {l: None for l in languages}),
            "language_version": _top(versions),
            "build_system": _top(build_systems),
            "services": services,
            "service_count": len(services),
            "db_type": db_types[0] if db_types else "",
            "orm": orms[0] if orms else "",
            "has_multi_module": any(b.parent_pom for b in self.backends),
        }


class TechStackDetector:
    """Unified tech stack detection — frontend + backend.

    Usage:
        detector = TechStackDetector()
        stack = detector.detect("D:/Desktop/BlueAlbum")
        # stack.frontend → FrameworkInfo(vue-3, 3.5.25)
        # stack.backends → [BackendInfo(spring-boot, java, 21), ...]
    """

    def __init__(self):
        self._frontend = FrameworkDetector()
        self.__backend = None  # lazy import to avoid circular deps

    @property
    def _backend_detector(self):
        if self.__backend is None:
            from aitest.discovery.source.backend_detector import BackendDetector
            self.__backend = BackendDetector()
        return self.__backend

    def detect(self, project_path: str | Path) -> TechStack:
        """Scan project for complete tech stack.

        - Frontend: package.json at root or 1-level subdir
        - Backend: pom.xml / build.gradle / requirements.txt at root or 1-level subdirs
        """
        root = Path(project_path).resolve()
        stack = TechStack(project_path=str(root))

        # Frontend
        stack.frontend = self._frontend.detect(root)

        # Backend
        try:
            stack.backends = self._backend_detector.detect(root)
        except Exception as e:
            logger.warning(f"Backend detection failed for {root}: {e}")

        return stack
