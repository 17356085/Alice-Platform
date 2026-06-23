"""
BackendDetector — reads pom.xml / build.gradle / requirements.txt etc.
→ detects backend framework, language, version, build system, DB, ORM.

Supports: Spring Boot (Maven/Gradle), Flask, FastAPI, Django, Express, Gin.
"""

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from aitest.knowledge_model.schema import (
    BackendFramework,
    BackendLanguage,
    BuildSystem,
    BackendInfo,
)

logger = logging.getLogger(__name__)

# ── Known DB driver → db_type mapping ───────────────────────────────────
DB_DRIVER_MAP = {
    "mysql-connector-j": "mysql",
    "mysql-connector-java": "mysql",
    "postgresql": "postgresql",
    "mssql-jdbc": "mssql",
    "h2": "h2",
    "mongodb-driver": "mongodb",
    "spring-boot-starter-data-mongodb": "mongodb",
    "sqlite-jdbc": "sqlite",
    "ojdbc": "oracle",
}

# ── Known ORM dependency → orm name mapping ─────────────────────────────
ORM_MAP = {
    "spring-boot-starter-data-jpa": "jpa",
    "mybatis-spring-boot-starter": "mybatis",
    "mybatis-plus-boot-starter": "mybatis-plus",
    "hibernate-core": "hibernate",
    "spring-boot-starter-data-mongodb": "spring-data-mongo",
}

# ── Spring Boot starter parent artifact IDs ────────────────────────────
SPRING_BOOT_PARENTS = {
    "spring-boot-starter-parent",
    "spring-boot-dependencies",
}


class BackendDetector:
    """Detect backend tech stack from build files and config.

    Usage:
        detector = BackendDetector()
        backends = detector.detect("D:/Desktop/BlueAlbum")
        # → [BackendInfo(SPRING_BOOT, JAVA, "21", MAVEN, ...), ...]
    """

    # ── Build file sniffing ────────────────────────────────────────────────

    # (filename, BuildSystem, is_backend)
    BUILD_SIGNATURES = [
        ("pom.xml", BuildSystem.MAVEN),
        ("build.gradle", BuildSystem.GRADLE),
        ("build.gradle.kts", BuildSystem.GRADLE),
        ("requirements.txt", BuildSystem.PIP),
        ("pyproject.toml", BuildSystem.POETRY),
        ("go.mod", BuildSystem.GO_MOD),
    ]

    @staticmethod
    def find_build_files(project_path: str | Path) -> list[tuple[Path, BuildSystem]]:
        """Scan root + 1-level subdirectories for backend build files.

        Returns list of (absolute_path, BuildSystem), sorted by depth.
        """
        root = Path(project_path).resolve()
        results: list[tuple[Path, BuildSystem]] = []

        # Root level
        for fname, bs in BackendDetector.BUILD_SIGNATURES:
            candidate = root / fname
            if candidate.exists():
                results.append((candidate, bs))

        # 1-level subdirectories (skip hidden, node_modules, front, .git)
        try:
            for d in sorted(root.iterdir()):
                if not d.is_dir():
                    continue
                if d.name.startswith('.') or d.name in ('node_modules',):
                    continue
                for fname, bs in BackendDetector.BUILD_SIGNATURES:
                    candidate = d / fname
                    if candidate.exists():
                        results.append((candidate, bs))
        except (PermissionError, OSError):
            pass

        return results

    # ── Main detection entry ────────────────────────────────────────────────

    def detect(self, project_path: str | Path) -> list[BackendInfo]:
        """Detect all backend services in project.

        For Maven multi-module: parent pom + one BackendInfo per child module.
        For single-module: one BackendInfo.
        Returns empty list if no backend detected.
        """
        root = Path(project_path).resolve()
        build_files = self.find_build_files(root)

        if not build_files:
            return []

        backends: list[BackendInfo] = []
        seen_roots: set[str] = set()

        for build_path, build_system in build_files:
            mod_root = str(build_path.parent.resolve())
            if mod_root in seen_roots:
                continue
            seen_roots.add(mod_root)

            if build_system == BuildSystem.MAVEN:
                info = self._detect_maven(build_path)
            elif build_system == BuildSystem.GRADLE:
                info = self._detect_gradle(build_path)
            elif build_system in (BuildSystem.PIP, BuildSystem.POETRY):
                info = self._detect_python(build_path, build_system)
            elif build_system == BuildSystem.GO_MOD:
                info = self._detect_go(build_path, build_system)
            else:
                info = BackendInfo(build_system=build_system, build_file=str(build_path))

            info.build_file = str(build_path)
            info.project_root = mod_root
            info.service_name = build_path.parent.name

            # Skip parent POMs (multi-module aggregators) — they get special treatment
            if info.parent_pom:
                # Still emit parent so caller knows about multi-module structure
                backends.append(info)
            elif info.framework != BackendFramework.UNKNOWN or info.language != BackendLanguage.UNKNOWN:
                backends.append(info)

        return backends

    # ── Maven / Spring Boot ─────────────────────────────────────────────────

    def _detect_maven(self, pom_path: Path) -> BackendInfo:
        """Parse pom.xml → BackendInfo."""
        info = BackendInfo(
            build_system=BuildSystem.MAVEN,
            language=BackendLanguage.JAVA,
            service_name=pom_path.parent.name,
        )

        try:
            tree = ET.parse(str(pom_path))
            root_el = tree.getroot()

            # XML namespace handling — pom.xml default namespace
            ns = ""
            if root_el.tag.startswith("{"):
                ns = root_el.tag.split("}")[0] + "}"

            # ── Parent POM detection ──
            parent_el = root_el.find(f"{ns}parent")
            if parent_el is not None:
                parent_artifact = self._text(parent_el, f"{ns}artifactId")
                parent_version = self._text(parent_el, f"{ns}version")
                parent_group = self._text(parent_el, f"{ns}groupId")

                if parent_artifact in SPRING_BOOT_PARENTS:
                    info.framework = BackendFramework.SPRING_BOOT
                    info.language_version = "17"  # default, overridden by <java.version>
                elif "spring-cloud" in (parent_artifact or ""):
                    info.framework = BackendFramework.SPRING_CLOUD
                elif "spring-boot" in (parent_artifact or ""):
                    info.framework = BackendFramework.SPRING_BOOT

            # ── Modules → parent POM ──
            modules_el = root_el.find(f"{ns}modules")
            if modules_el is not None:
                info.parent_pom = True
                for m_el in modules_el.findall(f"{ns}module"):
                    if m_el.text:
                        info.modules.append(m_el.text.strip())

            # ── Properties (java.version) ──
            props_el = root_el.find(f"{ns}properties")
            if props_el is not None:
                java_ver = self._text(props_el, f"{ns}java.version")
                if java_ver:
                    info.language_version = java_ver
                kotlin_ver = self._text(props_el, f"{ns}kotlin.version")
                if kotlin_ver:
                    info.language = BackendLanguage.KOTLIN

            # ── Dependencies → DB + ORM + framework confirmation ──
            deps_el = root_el.find(f"{ns}dependencies")
            if deps_el is not None:
                for dep_el in deps_el.findall(f"{ns}dependency"):
                    aid = self._text(dep_el, f"{ns}artifactId") or ""
                    gid = self._text(dep_el, f"{ns}groupId") or ""

                    # DB detection
                    if aid in DB_DRIVER_MAP:
                        info.db_type = DB_DRIVER_MAP[aid]
                    elif any(kw in aid.lower() for kw in ("mysql", "postgresql", "mongodb")):
                        for driver_key, db_name in DB_DRIVER_MAP.items():
                            if driver_key in aid:
                                info.db_type = db_name
                                break

                    # ORM detection
                    if aid in ORM_MAP:
                        info.orm = ORM_MAP[aid]

                    # Spring Boot starter presence confirms framework
                    if "spring-boot-starter" in aid and info.framework == BackendFramework.UNKNOWN:
                        info.framework = BackendFramework.SPRING_BOOT

                    # Spring Boot version from dependency management
                    if "spring-boot" in aid and info.framework == BackendFramework.UNKNOWN:
                        info.framework = BackendFramework.SPRING_BOOT

            # ── If Java but no framework detected, set UNKNOWN ──
            if info.framework == BackendFramework.UNKNOWN and info.language == BackendLanguage.JAVA:
                pass  # could be plain Java, leave as UNKNOWN

        except ET.ParseError as e:
            logger.warning(f"XML parse error in {pom_path}: {e}")
        except Exception as e:
            logger.warning(f"Error parsing {pom_path}: {e}")

        # ── Scan for application.yml / application.properties ──
        self._scan_config_files(pom_path.parent, info)

        return info

    def _detect_gradle(self, gradle_path: Path) -> BackendInfo:
        """Parse build.gradle(.kts) → BackendInfo."""
        info = BackendInfo(
            build_system=BuildSystem.GRADLE,
            language=BackendLanguage.JAVA,
            service_name=gradle_path.parent.name,
        )

        try:
            content = gradle_path.read_text(encoding="utf-8")

            # Spring Boot plugin
            if re.search(r"spring-boot", content, re.IGNORECASE):
                info.framework = BackendFramework.SPRING_BOOT

            # Kotlin
            if gradle_path.suffix == ".kts" or "kotlin" in content.lower():
                info.language = BackendLanguage.KOTLIN

            # Java version
            m = re.search(r"(?:sourceCompatibility|javaVersion)\s*[=:]\s*['\"]?(\d+)", content)
            if m:
                info.language_version = m.group(1)

            # DB driver
            for driver, db in DB_DRIVER_MAP.items():
                if driver in content:
                    info.db_type = db
                    break

            # ORM
            for dep, orm_name in ORM_MAP.items():
                if dep in content:
                    info.orm = orm_name
                    break

        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Error reading {gradle_path}: {e}")

        self._scan_config_files(gradle_path.parent, info)
        return info

    def _detect_python(self, build_path: Path, build_system: BuildSystem) -> BackendInfo:
        """Parse requirements.txt or pyproject.toml → BackendInfo."""
        info = BackendInfo(
            build_system=build_system,
            language=BackendLanguage.PYTHON,
            service_name=build_path.parent.name,
        )

        try:
            content = build_path.read_text(encoding="utf-8")

            # Framework detection
            lower = content.lower()
            if "fastapi" in lower:
                info.framework = BackendFramework.FASTAPI
            elif "flask" in lower:
                info.framework = BackendFramework.FLASK
            elif "django" in lower:
                info.framework = BackendFramework.DJANGO

            # Python version from pyproject.toml
            if build_system == BuildSystem.POETRY:
                m = re.search(r'python\s*=\s*["\']\^?~?(\d+\.\d+)', content)
                if m:
                    info.language_version = m.group(1)

        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Error reading {build_path}: {e}")

        return info

    def _detect_go(self, go_mod_path: Path, build_system: BuildSystem) -> BackendInfo:
        """Parse go.mod → BackendInfo."""
        info = BackendInfo(
            build_system=build_system,
            language=BackendLanguage.GO,
            service_name=go_mod_path.parent.name,
        )

        try:
            content = go_mod_path.read_text(encoding="utf-8")

            # Go version
            m = re.search(r"go\s+(\d+\.\d+)", content)
            if m:
                info.language_version = m.group(1)

            # Framework detection
            lower = content.lower()
            if "gin-gonic" in lower:
                info.framework = BackendFramework.GIN

        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Error reading {go_mod_path}: {e}")

        return info

    # ── Config file scanner ─────────────────────────────────────────────────

    @staticmethod
    def _scan_config_files(module_root: Path, info: BackendInfo):
        """Scan for application.yml / application.properties → DB info."""
        resource_dirs = [
            module_root / "src" / "main" / "resources",
            module_root / "src" / "resources",
            module_root / "resources",
            module_root / "config",
        ]

        for res_dir in resource_dirs:
            if not res_dir.is_dir():
                continue
            try:
                for cfg_file in sorted(res_dir.iterdir()):
                    name = cfg_file.name.lower()
                    if name in ("application.yml", "application.yaml",
                                "application.properties",
                                "application-dev.yml", "application-prod.yml"):
                        info.config_files.append(str(cfg_file))
                        # Try to extract DB info from application.yml
                        if info.db_type == "" and name in ("application.yml", "application.yaml"):
                            try:
                                content = cfg_file.read_text(encoding="utf-8")
                                BackendDetector._extract_db_from_yml(content, info)
                            except Exception:
                                pass
            except PermissionError:
                pass

    @staticmethod
    def _extract_db_from_yml(content: str, info: BackendInfo):
        """Extract DB type from Spring datasource config."""
        # datasource: url: jdbc:mysql://...
        m = re.search(r"url\s*:\s*jdbc:(\w+)://", content)
        if m:
            db = m.group(1).lower()
            if db in ("mysql", "postgresql", "mssql", "oracle", "h2"):
                info.db_type = db

    # ── XML helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _text(el, tag: str) -> Optional[str]:
        """Safely get text content of XML child element."""
        child = el.find(tag)
        return child.text.strip() if child is not None and child.text else None
