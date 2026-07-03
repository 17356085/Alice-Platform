"""API Parsers — parsing functions for API documentation.

Extracted from api_import.py for single-responsibility.
"""

import re
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _parse_openapi_summary(data: dict) -> dict:
    """解析 OpenAPI 摘要。"""
    endpoints = []
    groups = {}

    # OpenAPI 3.x
    if "openapi" in data:
        paths = data.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ("get", "post", "put", "delete", "patch"):
                    endpoint = {
                        "method": method.upper(),
                        "path": path,
                        "summary": details.get("summary", ""),
                        "tags": details.get("tags", []),
                    }
                    endpoints.append(endpoint)

                    # 按 tag 分组
                    for tag in details.get("tags", ["default"]):
                        if tag not in groups:
                            groups[tag] = []
                        groups[tag].append(endpoint)

    # Swagger 2.x
    elif "swagger" in data:
        paths = data.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ("get", "post", "put", "delete", "patch"):
                    endpoint = {
                        "method": method.upper(),
                        "path": path,
                        "summary": details.get("summary", ""),
                        "tags": details.get("tags", []),
                    }
                    endpoints.append(endpoint)

                    for tag in details.get("tags", ["default"]):
                        if tag not in groups:
                            groups[tag] = []
                        groups[tag].append(endpoint)

    return {
        "total_endpoints": len(endpoints),
        "endpoints": endpoints,
        "groups": {tag: len(eps) for tag, eps in groups.items()},
    }



def _parse_graphql_schema(content: str) -> dict:
    """解析 GraphQL Schema。"""
    import re

    queries = re.findall(r'type\s+Query\s*\{([^}]+)\}', content, re.DOTALL)
    mutations = re.findall(r'type\s+Mutation\s*\{([^}]+)\}', content, re.DOTALL)

    endpoints = []

    for query_block in queries:
        for line in query_block.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                name = line.split("(")[0].split(":")[0].strip()
                if name:
                    endpoints.append({
                        "method": "QUERY",
                        "path": name,
                        "summary": "",
                    })

    for mutation_block in mutations:
        for line in mutation_block.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                name = line.split("(")[0].split(":")[0].strip()
                if name:
                    endpoints.append({
                        "method": "MUTATION",
                        "path": name,
                        "summary": "",
                    })

    return {
        "total_endpoints": len(endpoints),
        "endpoints": endpoints,
        "groups": {"Query": len([e for e in endpoints if e["method"] == "QUERY"]),
                   "Mutation": len([e for e in endpoints if e["method"] == "MUTATION"])},
    }



def _parse_curl_commands(commands: str) -> list:
    """解析 cURL 命令。"""
    import re

    apis = []
    lines = commands.strip().split("\n")

    current_curl = ""
    for line in lines:
        line = line.strip()
        if line.startswith("curl"):
            if current_curl:
                api = _parse_single_curl(current_curl)
                if api:
                    apis.append(api)
            current_curl = line
        elif current_curl:
            current_curl += " " + line

    if current_curl:
        api = _parse_single_curl(current_curl)
        if api:
            apis.append(api)

    return apis



def _parse_single_curl(curl_cmd: str) -> Optional[dict]:
    """解析单个 cURL 命令。"""
    import re

    # 提取 URL
    url_match = re.search(r"'([^']+)'", curl_cmd)
    if not url_match:
        url_match = re.search(r'"([^"]+)"', curl_cmd)
    if not url_match:
        url_match = re.search(r'curl\s+(\S+)', curl_cmd)

    if not url_match:
        return None

    url = url_match.group(1)

    # 提取方法
    method = "GET"
    method_match = re.search(r'-X\s+(\w+)', curl_cmd)
    if method_match:
        method = method_match.group(1).upper()
    elif "data" in curl_cmd or "-d" in curl_cmd:
        method = "POST"

    # 提取路径
    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = parsed.path

    return {
        "method": method,
        "path": path,
        "summary": "",
    }



def _scan_python_routes(content: str, file_path: str) -> list:
    """扫描 Python 文件中的 FastAPI / Flask 路由。"""
    import re

    apis = []

    # FastAPI / Flask 路由装饰器
    patterns = [
        r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        r'@\w+\.route\s*\(\s*["\']([^"\']+)["\'].*methods\s*=\s*\[["\'](\w+)["\']',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if len(match) == 2:
                method, path = match
                apis.append({
                    "method": method.upper(),
                    "path": path,
                    "summary": "",
                    "source": file_path,
                })

    return apis



def _scan_java_routes(content: str, file_path: str) -> list:
    """扫描 Java 文件中的 Spring Boot 注解。"""
    import re

    apis = []

    # Spring Boot 注解
    patterns = [
        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(\s*["\']([^"\']+)["\']',
        r'@RequestMapping\s*\(\s*value\s*=\s*["\']([^"\']+)["\'].*method\s*=\s*RequestMethod\.(\w+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if len(match) == 2:
                annotation, path = match
                method = annotation.replace("Mapping", "").upper()
                apis.append({
                    "method": method,
                    "path": path,
                    "summary": "",
                    "source": file_path,
                })

    return apis



def _parse_doc_with_llm(content: str, file_type: str) -> Optional[dict]:
    """使用 LLM 解析文档。"""
    # TODO: 实现 LLM 解析
    console.print("[yellow]⚠️  LLM 解析尚未实现[/yellow]")
    return None


