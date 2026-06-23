"""
ApiExtractor — scan source files → ApiMetadata list.

Extracts API calls from:
  - axios calls: axios.get('/api/user/list'), axios.post(...)
  - fetch calls: fetch('/api/user/list')
  - Request wrapper: request.get('/api/user/list')
  - umi-request: request('/api/user/list')

Also reads OpenAPI/Swagger spec files if present.

Establishes page → API mapping by tracking which component files make each API call.
"""

import json
import logging
import re
from pathlib import Path

from aitest.knowledge_model.schema import (
    ApiMetadata, FrameworkInfo,
)
from aitest.knowledge_model.provenance import FieldValue, Source
from aitest.discovery.source.file_indexer import FileIndex
from .base import BaseExtractor

logger = logging.getLogger(__name__)

# ── API call patterns ────────────────────────────────────────────────────

# axios / request wrapper calls
AXIOS_RE = re.compile(
    r"""(?:axios|request|http|api|service)\s*\.\s*
        (get|post|put|delete|patch|head|options)\s*\(\s*
        ['\"]([^'\"]+)['\"]""",
    re.IGNORECASE | re.VERBOSE
)

# axios direct: axios({ method: 'get', url: '/api/...' })
AXIOS_CONFIG_RE = re.compile(
    r"""(?:axios|request|http)\s*\(\s*\{[^}]*?
        (?:method|type)\s*:\s*['\"](get|post|put|delete|patch)['\"][^}]*?
        url\s*:\s*['\"]([^'\"]+)['\"]""",
    re.IGNORECASE | re.VERBOSE | re.DOTALL
)

# fetch calls
FETCH_RE = re.compile(
    r"""fetch\s*\(\s*['\"]([^'\"]+)['\"]
        \s*(?:,\s*\{[^}]*?(?:method|type)\s*:\s*['\"](get|post|put|delete|patch)['\"][^}]*?\})?""",
    re.IGNORECASE | re.VERBOSE | re.DOTALL
)

# umi-request / @tanstack/react-query
UMI_RE = re.compile(
    r"""request\s*\(\s*['\"]([^'\"]+)['\"]
        \s*(?:,\s*\{[^}]*?(?:method|type)\s*:\s*['\"](get|post|put|delete|patch)['\"][^}]*?\})?""",
    re.IGNORECASE | re.VERBOSE | re.DOTALL
)

# OpenAPI path detection
OPENAPI_FILES = ["openapi.json", "openapi.yaml", "swagger.json", "swagger.yaml",
                 "api-docs.json", "api-spec.json", "spec.json"]


class ApiExtractor(BaseExtractor):
    """
    Extract API endpoints from source code and OpenAPI specs.

    Usage:
        extractor = ApiExtractor(project_root, framework, file_index)
        apis = extractor.extract()
        for api in apis:
            print(f"{api.method.value} {api.path.value}")
    """

    def can_extract(self) -> bool:
        return (
            len(self.file_index.api_files) > 0
            or len(self.file_index.view_files) > 0
        )

    def extract(self) -> list[ApiMetadata]:
        apis = []

        # 1. Extract from API service files
        for api_file in self.file_index.api_files:
            content = self.read_file(api_file)
            if not content:
                continue
            file_apis = self._parse_api_calls(content, api_file)
            apis.extend(file_apis)

        # 2. Extract from view files (page → API mapping)
        for view_file in self.file_index.view_files:
            content = self.read_file(view_file)
            if not content:
                continue
            view_apis = self._parse_api_calls(content, view_file)
            # Tag with calling page for mapping
            page_id = view_file.stem.lower().replace(" ", "-")
            for api in view_apis:
                api.called_by_pages.append(page_id)
                api.called_by_components.append(view_file.stem)
            apis.extend(view_apis)

        # 3. Try OpenAPI spec
        openapi_apis = self._parse_openapi_specs()
        apis.extend(openapi_apis)

        # Deduplicate by method + path
        seen = set()
        unique = []
        for api in apis:
            key = (api.method.value, api.path.value)
            if key not in seen:
                seen.add(key)
                unique.append(api)

        logger.info(f"Extracted {len(unique)} unique API endpoints ({len(apis)} raw)")
        return unique

    def _parse_api_calls(self, content: str, file_path: Path) -> list[ApiMetadata]:
        apis = []
        detail = file_path.name

        # axios.method('/api/...')
        for match in AXIOS_RE.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            apis.append(ApiMetadata(
                method=FieldValue.certain(method, Source.VUE_COMPONENT, detail),
                path=FieldValue.certain(path, Source.VUE_COMPONENT, detail),
                description=FieldValue.inferred(f"{method} {path}"),
                source_file=str(file_path),
                http_client="axios",
            ))

        # axios({ method: 'get', url: '...' })
        for match in AXIOS_CONFIG_RE.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            apis.append(ApiMetadata(
                method=FieldValue.certain(method, Source.VUE_COMPONENT, detail),
                path=FieldValue.certain(path, Source.VUE_COMPONENT, detail),
                description=FieldValue.inferred(f"{method} {path}"),
                source_file=str(file_path),
                http_client="axios",
            ))

        # fetch('/api/...')
        for match in FETCH_RE.finditer(content):
            path = match.group(1)
            method = match.group(2).upper() if match.lastindex and match.lastindex >= 2 and match.group(2) else "GET"
            apis.append(ApiMetadata(
                method=FieldValue.certain(method, Source.VUE_COMPONENT, detail),
                path=FieldValue.certain(path, Source.VUE_COMPONENT, detail),
                description=FieldValue.inferred(f"{method} {path}"),
                source_file=str(file_path),
                http_client="fetch",
            ))

        return apis

    def _parse_openapi_specs(self) -> list[ApiMetadata]:
        """Parse OpenAPI/Swagger spec files if present."""
        apis = []
        for filename in OPENAPI_FILES:
            spec_path = self.project_root / filename
            if not spec_path.exists():
                # Also try src/ subdirectory
                spec_path = self.project_root / "src" / filename
            if not spec_path.exists():
                continue

            try:
                spec = self._read_json_or_yaml(spec_path)
                if not spec:
                    continue

                paths = spec.get("paths", {})
                for path, methods in paths.items():
                    for method, details in methods.items():
                        if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                            apis.append(ApiMetadata(
                                method=FieldValue.certain(method.upper(), Source.OPENAPI, spec_path.name),
                                path=FieldValue.certain(path, Source.OPENAPI, spec_path.name),
                                description=FieldValue.certain(
                                    details.get("summary", details.get("description", "")),
                                    Source.OPENAPI, spec_path.name
                                ),
                                source_file=str(spec_path),
                                http_client="",
                            ))
                logger.info(f"Parsed {len(apis)} endpoints from {spec_path.name}")
            except Exception as e:
                logger.warning(f"Failed to parse OpenAPI spec {spec_path}: {e}")

        return apis

    @staticmethod
    def _read_json_or_yaml(path: Path) -> dict:
        content = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml"):
            try:
                import yaml
                return yaml.safe_load(content) or {}
            except ImportError:
                logger.warning("yaml module not available for OpenAPI parsing")
                return {}
        return json.loads(content)
