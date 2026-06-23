"""
VueComponentExtractor — parse .vue SFC files → ComponentMetadata + ElementInfo.

Extracts:
  - Template elements: el-button, el-table, el-dialog, el-input, etc.
  - Script setup: imports, props, emits, reactive state
  - Component name from <script> or filename

Strategy: regex for template (fast, handles ~80%), AST for complex cases.

Output: list[ComponentMetadata]
"""

import logging
import re
from pathlib import Path
from typing import Optional

from aitest.knowledge_model.schema import (
    ComponentMetadata, ComponentRef, ElementInfo, FrameworkInfo,
)
from aitest.knowledge_model.provenance import FieldValue, Source
from aitest.discovery.source.file_indexer import FileIndex
from .base import BaseExtractor

logger = logging.getLogger(__name__)

# ── Template element patterns ────────────────────────────────────────────

# Extract individual HTML elements from template
TEMPLATE_RE = re.compile(r'<template[^>]*>([\s\S]*?)</template>', re.DOTALL)
SCRIPT_RE = re.compile(r'<script[^>]*>([\s\S]*?)</script>', re.DOTALL)
SCRIPT_SETUP_RE = re.compile(r'<script\s+setup[^>]*>([\s\S]*?)</script>', re.DOTALL)

# Import statements in script
SCRIPT_IMPORT_RE = re.compile(
    r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]"
)

# UI element patterns — Element Plus, Ant Design Vue, Naive UI, etc.
UI_ELEMENT_PATTERNS = {
    "button": [
        r'<(?:el|a|n)-button[^>]*>([^<]*)</(?:el|a|n)-button>',
        r'<button[^>]*>',
    ],
    "input": [
        r'<(?:el|a|n)-input[^>]*/?>',
        r'<input[^>]*>',
    ],
    "select": [
        r'<(?:el|a|n)-select[^>]*>',
        r'<select[^>]*>',
    ],
    "table": [
        r'<(?:el|a|n)-table[^>]*>',
        r'<table[^>]*>',
    ],
    "dialog": [
        r'<(?:el|a|n)-dialog[^>]*>',
        r'<(?:el|a|n)-drawer[^>]*>',
    ],
    "form": [
        r'<(?:el|a|n)-form[^>]*>',
        r'<form[^>]*>',
    ],
    "tabs": [
        r'<(?:el|a|n)-tabs[^>]*>',
    ],
    "pagination": [
        r'<(?:el|a|n)-pagination[^>]*>',
    ],
    "tree": [
        r'<(?:el|a|n)-tree[^>]*>',
    ],
    "upload": [
        r'<(?:el|a|n)-upload[^>]*>',
    ],
    "cascader": [
        r'<(?:el|a|n)-cascader[^>]*>',
    ],
    "date_picker": [
        r'<(?:el|a|n)-date-picker[^>]*>',
    ],
}

# Label extraction from element attributes
LABEL_RE = re.compile(r'label\s*=\s*["\']([^"\']+)["\']')
PLACEHOLDER_RE = re.compile(r'placeholder\s*=\s*["\']([^"\']+)["\']')
PROP_RE = re.compile(r'prop\s*=\s*["\']([^"\']+)["\']')


class VueComponentExtractor(BaseExtractor):
    """
    Parse .vue SFC files → ComponentMetadata list.

    Usage:
        extractor = VueComponentExtractor(project_root, framework, file_index)
        components = extractor.extract()
        for comp in components:
            print(f"{comp.component_name.value}: {len(comp.template_elements)} elements")
    """

    def can_extract(self) -> bool:
        return len(self.file_index.view_files) > 0

    def extract(self) -> list[ComponentMetadata]:
        components = []
        for vue_file in self.file_index.view_files:
            try:
                comp = self._parse_vue_file(vue_file)
                if comp:
                    components.append(comp)
            except Exception as e:
                logger.warning(f"Failed to parse {vue_file.name}: {e}")

        # Also parse key components from component_files
        for comp_file in self.file_index.component_files[:50]:  # Limit to avoid bloat
            try:
                comp = self._parse_vue_file(comp_file)
                if comp:
                    components.append(comp)
            except Exception:
                pass

        logger.info(f"Extracted {len(components)} component metadata objects")
        return components

    def _parse_vue_file(self, file_path: Path) -> Optional[ComponentMetadata]:
        content = self.read_file(file_path)
        if not content:
            return None

        detail = str(file_path.relative_to(self.project_root)) if self.project_root in file_path.parents else file_path.name
        rv = lambda v: FieldValue.certain(v, Source.VUE_COMPONENT, detail)

        # Extract template
        template = ""
        tm = TEMPLATE_RE.search(content)
        if tm:
            template = tm.group(1)

        # Extract script
        has_setup = False
        script = ""
        sm = SCRIPT_SETUP_RE.search(content)
        if sm:
            script = sm.group(1)
            has_setup = True
        else:
            sm = SCRIPT_RE.search(content)
            if sm:
                script = sm.group(1)

        # Component name — from filename
        comp_name = file_path.stem  # "UserList" from "UserList.vue"

        # Extract template elements
        elements = self._extract_elements(template)

        # Extract imports (child components)
        imports = self._extract_imports(script, file_path)

        # Extract props/emits
        props = self._extract_props(script, content)
        emits = self._extract_emits(script, content)

        # Detect component type
        comp_type = self._detect_type(file_path, template)

        return ComponentMetadata(
            file_path=rv(str(file_path)),
            component_name=rv(comp_name),
            component_type=rv(comp_type),
            template_elements=elements,
            imports=imports,
            script_setup=has_setup,
            props=props,
            emits=emits,
        )

    def _extract_elements(self, template: str) -> list[ElementInfo]:
        elements = []
        for elem_type, patterns in UI_ELEMENT_PATTERNS.items():
            for pat in patterns:
                for match in re.finditer(pat, template, re.DOTALL):
                    element_text = match.group(0)
                    label = ""
                    lm = LABEL_RE.search(element_text)
                    if lm:
                        label = lm.group(1)
                    pl = PLACEHOLDER_RE.search(element_text)
                    if pl and not label:
                        label = pl.group(1)
                    pr = PROP_RE.search(element_text)
                    if pr and not label:
                        label = pr.group(1)

                    elements.append(ElementInfo(
                        label=label or elem_type,
                        type=elem_type,
                        source=Source.VUE_COMPONENT,
                        confidence=0.85,
                    ))
        return elements

    def _extract_imports(self, script: str, file_path: Path) -> list[ComponentRef]:
        imports = []
        for match in SCRIPT_IMPORT_RE.finditer(script):
            name = match.group(1)
            path = match.group(2)
            if name[0].isupper():  # Vue component imports are PascalCase
                imports.append(ComponentRef(
                    name=name,
                    path=path,
                    source=Source.VUE_COMPONENT,
                ))
        return imports

    def _extract_props(self, script: str, full_content: str) -> list[str]:
        # defineProps(['visible', 'data'])
        dp = re.search(r'defineProps\s*\(\s*\[([^\]]+)\]', full_content)
        if dp:
            return [x.strip().strip("'\"") for x in dp.group(1).split(",")]
        # defineProps<{ visible: boolean }>()
        dp2 = re.search(r'defineProps\s*<\s*\{([^}]+)\}', full_content)
        if dp2:
            return [x.strip().split(":")[0].strip() for x in dp2.group(1).split(";") if x.strip()]
        return []

    def _extract_emits(self, script: str, full_content: str) -> list[str]:
        de = re.search(r'defineEmits\s*\(\s*\[([^\]]+)\]', full_content)
        if de:
            return [x.strip().strip("'\"") for x in de.group(1).split(",")]
        return []

    def _detect_type(self, file_path: Path, template: str) -> str:
        path_str = str(file_path).lower()
        if "dialog" in path_str or "modal" in path_str or "drawer" in path_str:
            return "dialog"
        if "layout" in path_str:
            return "layout"
        if "widget" in path_str or "card" in path_str:
            return "widget"
        if "component" in path_str.split("/")[-2:]:
            return "widget"
        return "page"
