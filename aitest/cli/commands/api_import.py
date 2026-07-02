"""
API 文档导入 — 支持多种 API 文档格式。

支持的格式:
  - Swagger UI / Knife4j URL
  - OpenAPI 文件 (JSON/YAML)
  - Postman Collection
  - Apifox / RAP / YAPI 导出
  - GraphQL Schema
  - HAR 文件 (浏览器抓包)
  - cURL 命令
  - 源码目录 (扫描注解)
  - Markdown / Excel / 其他文件
"""

import json
from pathlib import Path
from typing import Optional
import yaml

from rich.console import Console
from rich.table import Table

console = Console()


# ── API 文档来源定义 ──────────────────────────────────────────────

API_SOURCES = {
    "1": {"name": "Swagger UI / Knife4j URL", "handler": "swagger_url"},
    "2": {"name": "OpenAPI 文件 (JSON/YAML)", "handler": "openapi_file"},
    "3": {"name": "Postman Collection", "handler": "postman"},
    "4": {"name": "Apifox / RAP / YAPI 导出", "handler": "apifox"},
    "5": {"name": "GraphQL Schema", "handler": "graphql"},
    "6": {"name": "HAR 文件 (浏览器抓包)", "handler": "har"},
    "7": {"name": "cURL 命令", "handler": "curl"},
    "8": {"name": "源码目录 (自动扫描注解)", "handler": "source_scan"},
    "9": {"name": "Markdown / Excel / 其他文件", "handler": "file"},
    "10": {"name": "跳过", "handler": "skip"},
}


# ── 主入口 ──────────────────────────────────────────────────────

def ask_api_doc() -> Optional[dict]:
    """询问 API 文档。

    Returns:
        API 文档配置，或 None (跳过)
    """
    has_api = Confirm.ask("\n是否有 API 文档?", default=False)

    if not has_api:
        return None

    # 显示来源选项
    console.print("\nAPI 文档来源:")
    for key, source in API_SOURCES.items():
        console.print(f"  [{key}] {source['name']}")

    choice = Prompt.ask("选择", choices=list(API_SOURCES.keys()), default="10")

    if choice == "10":
        return None

    handler = API_SOURCES[choice]["handler"]
    return _handle_source(handler)


def import_api_doc(api_config: dict, tlo_dir: Path) -> dict:
    """导入 API 文档。

    Args:
        api_config: API 文档配置
        tlo_dir: .tlo 目录路径

    Returns:
        导入结果
    """
    if not api_config:
        return None

    source_type = api_config.get("type")
    api_dir = tlo_dir / "api"
    api_dir.mkdir(parents=True, exist_ok=True)

    # 根据来源类型处理
    handlers = {
        "swagger_url": _import_swagger_url,
        "openapi_file": _import_openapi_file,
        "postman": _import_postman,
        "apifox": _import_apifox,
        "graphql": _import_graphql,
        "har": _import_har,
        "curl": _import_curl,
        "source_scan": _import_source_scan,
        "file": _import_file,
    }

    handler = handlers.get(source_type)
    if not handler:
        console.print(f"[red]❌ 不支持的来源类型: {source_type}[/red]")
        return None

    return handler(api_config, api_dir)


def _handle_source(handler: str) -> dict:
    """处理来源选择。"""
    if handler == "swagger_url":
        url = Prompt.ask("Swagger UI 地址")
        return {"type": "swagger_url", "url": url}
    elif handler == "openapi_file":
        path = Prompt.ask("文件路径")
        return {"type": "openapi_file", "path": path}
    elif handler == "postman":
        path = Prompt.ask("Postman Collection 路径")
        return {"type": "postman", "path": path}
    elif handler == "apifox":
        path = Prompt.ask("Apifox / RAP / YAPI 导出文件路径")
        return {"type": "apifox", "path": path}
    elif handler == "graphql":
        source = Prompt.ask("GraphQL Schema (URL 或文件路径)")
        return {"type": "graphql", "source": source}
    elif handler == "har":
        path = Prompt.ask("HAR 文件路径")
        return {"type": "har", "path": path}
    elif handler == "curl":
        console.print("粘贴 cURL 命令 (多行，空行结束):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        return {"type": "curl", "commands": "\n".join(lines)}
    elif handler == "source_scan":
        path = Prompt.ask("源码目录路径")
        return {"type": "source_scan", "path": path}
    elif handler == "file":
        path = Prompt.ask("文件路径 (Markdown / Excel / 其他)")
        return {"type": "file", "path": path}

    return None


# ── 导入处理器 ──────────────────────────────────────────────────

def _import_swagger_url(config: dict, api_dir: Path) -> dict:
    """从 Swagger UI URL 导入。"""
    url = config.get("url", "")
    console.print(f"\n🔍 正在从 {url} 获取 API 文档...")

    try:
        import httpx

        # 尝试常见的 Swagger JSON 路径
        swagger_paths = [
            "/v2/api-docs",
            "/api-docs",
            "/swagger.json",
            "/swagger/v1/swagger.json",
            "/api-docs/v1",
        ]

        openapi_data = None
        for path in swagger_paths:
            try:
                full_url = url.rstrip("/") + path
                response = httpx.get(full_url, timeout=30, follow_redirects=True)
                if response.status_code == 200:
                    data = response.json()
                    if "swagger" in data or "openapi" in data:
                        openapi_data = data
                        console.print(f"  [green]✅ 找到 API 文档: {path}[/green]")
                        break
            except Exception:
                continue

        if not openapi_data:
            # 尝试直接访问 URL
            try:
                response = httpx.get(url, timeout=30, follow_redirects=True)
                if response.status_code == 200:
                    data = response.json()
                    if "swagger" in data or "openapi" in data:
                        openapi_data = data
            except Exception:
                pass

        if not openapi_data:
            console.print("[red]❌ 无法获取 API 文档[/red]")
            console.print("[yellow]请确保 Swagger UI 地址正确，且服务已启动[/yellow]")
            return None

        # 保存
        with open(api_dir / "openapi.json", "w", encoding="utf-8") as f:
            json.dump(openapi_data, f, ensure_ascii=False, indent=2)

        # 解析摘要
        summary = _parse_openapi_summary(openapi_data)
        _save_summary(summary, api_dir)

        console.print(f"  [green]✅ 发现 {summary['total_endpoints']} 个 API 端点[/green]")
        return summary

    except Exception as e:
        console.print(f"[red]❌ 导入失败: {e}[/red]")
        return None


def _import_openapi_file(config: dict, api_dir: Path) -> dict:
    """从 OpenAPI 文件导入。"""
    file_path = Path(config.get("path", ""))

    if not file_path.exists():
        console.print(f"[red]❌ 文件不存在: {file_path}[/red]")
        return None

    console.print(f"\n📄 正在读取 {file_path.name}...")

    try:
        content = file_path.read_text(encoding="utf-8")

        # 根据扩展名解析
        if file_path.suffix in (".json",):
            data = json.loads(content)
        elif file_path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(content)
        else:
            console.print(f"[red]❌ 不支持的文件格式: {file_path.suffix}[/red]")
            return None

        # 验证是否为 OpenAPI
        if "swagger" not in data and "openapi" not in data:
            console.print("[yellow]⚠️  文件可能不是 OpenAPI 格式[/yellow]")

        # 保存
        with open(api_dir / "openapi.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 解析摘要
        summary = _parse_openapi_summary(data)
        _save_summary(summary, api_dir)

        console.print(f"  [green]✅ 发现 {summary['total_endpoints']} 个 API 端点[/green]")
        return summary

    except Exception as e:
        console.print(f"[red]❌ 导入失败: {e}[/red]")
        return None


def _import_postman(config: dict, api_dir: Path) -> dict:
    """从 Postman Collection 导入。"""
    file_path = Path(config.get("path", ""))

    if not file_path.exists():
        console.print(f"[red]❌ 文件不存在: {file_path}[/red]")
        return None

    console.print(f"\n📄 正在读取 Postman Collection: {file_path.name}...")

    try:
        content = file_path.read_text(encoding="utf-8")
        data = json.loads(content)

        # 转换为 OpenAPI 格式
        openapi_data = _convert_postman_to_openapi(data)

        # 保存
        with open(api_dir / "openapi.json", "w", encoding="utf-8") as f:
            json.dump(openapi_data, f, ensure_ascii=False, indent=2)

        # 保存原始文件
        raw_dir = api_dir / "raw"
        raw_dir.mkdir(exist_ok=True)
        with open(raw_dir / file_path.name, "w", encoding="utf-8") as f:
            f.write(content)

        # 解析摘要
        summary = _parse_openapi_summary(openapi_data)
        _save_summary(summary, api_dir)

        console.print(f"  [green]✅ 发现 {summary['total_endpoints']} 个 API 端点[/green]")
        return summary

    except Exception as e:
        console.print(f"[red]❌ 导入失败: {e}[/red]")
        return None


def _import_apifox(config: dict, api_dir: Path) -> dict:
    """从 Apifox / RAP / YAPI 导出导入。"""
    file_path = Path(config.get("path", ""))

    if not file_path.exists():
        console.print(f"[red]❌ 文件不存在: {file_path}[/red]")
        return None

    console.print(f"\n📄 正在读取: {file_path.name}...")

    try:
        content = file_path.read_text(encoding="utf-8")
        data = json.loads(content)

        # 尝试检测格式
        if "swagger" in data or "openapi" in data:
            # 已经是 OpenAPI 格式
            openapi_data = data
        elif "item" in data:
            # Postman 格式
            openapi_data = _convert_postman_to_openapi(data)
        elif "data" in data and "interfaces" in data.get("data", {}):
            # RAP / YAPI 格式
            openapi_data = _convert_rap_to_openapi(data)
        else:
            console.print("[yellow]⚠️  无法识别格式，尝试按 OpenAPI 解析[/yellow]")
            openapi_data = data

        # 保存
        with open(api_dir / "openapi.json", "w", encoding="utf-8") as f:
            json.dump(openapi_data, f, ensure_ascii=False, indent=2)

        # 保存原始文件
        raw_dir = api_dir / "raw"
        raw_dir.mkdir(exist_ok=True)
        with open(raw_dir / file_path.name, "w", encoding="utf-8") as f:
            f.write(content)

        # 解析摘要
        summary = _parse_openapi_summary(openapi_data)
        _save_summary(summary, api_dir)

        console.print(f"  [green]✅ 发现 {summary['total_endpoints']} 个 API 端点[/green]")
        return summary

    except Exception as e:
        console.print(f"[red]❌ 导入失败: {e}[/red]")
        return None


def _import_graphql(config: dict, api_dir: Path) -> dict:
    """从 GraphQL Schema 导入。"""
    source = config.get("source", "")

    console.print(f"\n🔍 正在读取 GraphQL Schema...")

    try:
        schema_content = None

        # 判断是 URL 还是文件
        if source.startswith("http"):
            import httpx
            response = httpx.get(source, timeout=30)
            if response.status_code == 200:
                schema_content = response.text
        else:
            file_path = Path(source)
            if file_path.exists():
                schema_content = file_path.read_text(encoding="utf-8")

        if not schema_content:
            console.print("[red]❌ 无法获取 GraphQL Schema[/red]")
            return None

        # 解析 GraphQL Schema
        summary = _parse_graphql_schema(schema_content)

        # 保存
        with open(api_dir / "graphql_schema.graphql", "w", encoding="utf-8") as f:
            f.write(schema_content)

        _save_summary(summary, api_dir)

        console.print(f"  [green]✅ 发现 {summary['total_endpoints']} 个 Query/Mutation[/green]")
        return summary

    except Exception as e:
        console.print(f"[red]❌ 导入失败: {e}[/red]")
        return None


def _import_har(config: dict, api_dir: Path) -> dict:
    """从 HAR 文件导入。"""
    file_path = Path(config.get("path", ""))

    if not file_path.exists():
        console.print(f"[red]❌ 文件不存在: {file_path}[/red]")
        return None

    console.print(f"\n📄 正在解析 HAR 文件: {file_path.name}...")

    try:
        content = file_path.read_text(encoding="utf-8")
        har_data = json.loads(content)

        # 提取 API 请求
        entries = har_data.get("log", {}).get("entries", [])
        apis = []

        for entry in entries:
            request = entry.get("request", {})
            response = entry.get("response", {})

            method = request.get("method", "")
            url = request.get("url", "")

            # 过滤非 API 请求
            if not url or method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                continue

            # 提取路径
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path

            # 过滤静态资源
            if any(path.endswith(ext) for ext in (".js", ".css", ".png", ".jpg", ".gif", ".svg")):
                continue

            apis.append({
                "method": method,
                "path": path,
                "status": response.get("status", 0),
            })

        # 去重
        unique_apis = []
        seen = set()
        for api in apis:
            key = f"{api['method']} {api['path']}"
            if key not in seen:
                seen.add(key)
                unique_apis.append(api)

        # 构建 OpenAPI 格式
        openapi_data = _build_openapi_from_apis(unique_apis)

        # 保存
        with open(api_dir / "openapi.json", "w", encoding="utf-8") as f:
            json.dump(openapi_data, f, ensure_ascii=False, indent=2)

        # 保存原始文件
        raw_dir = api_dir / "raw"
        raw_dir.mkdir(exist_ok=True)
        with open(raw_dir / file_path.name, "w", encoding="utf-8") as f:
            f.write(content)

        # 解析摘要
        summary = _parse_openapi_summary(openapi_data)
        _save_summary(summary, api_dir)

        console.print(f"  [green]✅ 发现 {summary['total_endpoints']} 个 API 端点[/green]")
        return summary

    except Exception as e:
        console.print(f"[red]❌ 导入失败: {e}[/red]")
        return None


def _import_curl(config: dict, api_dir: Path) -> dict:
    """从 cURL 命令导入。"""
    commands = config.get("commands", "")

    console.print(f"\n🔍 正在解析 cURL 命令...")

    try:
        # 解析 cURL 命令
        apis = _parse_curl_commands(commands)

        if not apis:
            console.print("[yellow]⚠️  未解析到 API 请求[/yellow]")
            return None

        # 构建 OpenAPI 格式
        openapi_data = _build_openapi_from_apis(apis)

        # 保存
        with open(api_dir / "openapi.json", "w", encoding="utf-8") as f:
            json.dump(openapi_data, f, ensure_ascii=False, indent=2)

        # 保存原始命令
        with open(api_dir / "curl_commands.txt", "w", encoding="utf-8") as f:
            f.write(commands)

        # 解析摘要
        summary = _parse_openapi_summary(openapi_data)
        _save_summary(summary, api_dir)

        console.print(f"  [green]✅ 发现 {summary['total_endpoints']} 个 API 端点[/green]")
        return summary

    except Exception as e:
        console.print(f"[red]❌ 导入失败: {e}[/red]")
        return None


def _import_source_scan(config: dict, api_dir: Path) -> dict:
    """从源码目录扫描注解。"""
    source_path = Path(config.get("path", ""))

    if not source_path.exists():
        console.print(f"[red]❌ 目录不存在: {source_path}[/red]")
        return None

    console.print(f"\n🔍 正在扫描源码目录: {source_path}...")

    try:
        # 扫描 Python 文件中的 FastAPI / Flask 路由
        apis = []

        for py_file in source_path.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            found = _scan_python_routes(content, str(py_file))
            apis.extend(found)

        # 扫描 Java 文件中的 Spring Boot 注解
        for java_file in source_path.rglob("*.java"):
            content = java_file.read_text(encoding="utf-8")
            found = _scan_java_routes(content, str(java_file))
            apis.extend(found)

        if not apis:
            console.print("[yellow]⚠️  未扫描到 API 路由[/yellow]")
            return None

        # 构建 OpenAPI 格式
        openapi_data = _build_openapi_from_apis(apis)

        # 保存
        with open(api_dir / "openapi.json", "w", encoding="utf-8") as f:
            json.dump(openapi_data, f, ensure_ascii=False, indent=2)

        # 解析摘要
        summary = _parse_openapi_summary(openapi_data)
        _save_summary(summary, api_dir)

        console.print(f"  [green]✅ 发现 {summary['total_endpoints']} 个 API 端点[/green]")
        return summary

    except Exception as e:
        console.print(f"[red]❌ 导入失败: {e}[/red]")
        return None


def _import_file(config: dict, api_dir: Path) -> dict:
    """从 Markdown / Excel / 其他文件导入。"""
    file_path = Path(config.get("path", ""))

    if not file_path.exists():
        console.print(f"[red]❌ 文件不存在: {file_path}[/red]")
        return None

    console.print(f"\n📄 正在读取文件: {file_path.name}...")

    try:
        content = file_path.read_text(encoding="utf-8")

        # 使用 LLM 解析文档
        console.print("  🔍 使用 AI 解析文档...")
        summary = _parse_doc_with_llm(content, file_path.suffix)

        if not summary:
            console.print("[yellow]⚠️  无法解析文档内容[/yellow]")
            return None

        # 保存原始文件
        raw_dir = api_dir / "raw"
        raw_dir.mkdir(exist_ok=True)
        with open(raw_dir / file_path.name, "w", encoding="utf-8") as f:
            f.write(content)

        _save_summary(summary, api_dir)

        console.print(f"  [green]✅ 发现 {summary['total_endpoints']} 个 API 端点[/green]")
        return summary

    except Exception as e:
        console.print(f"[red]❌ 导入失败: {e}[/red]")
        return None


# ── 解析工具 ──────────────────────────────────────────────────

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


def _convert_postman_to_openapi(data: dict) -> dict:
    """转换 Postman Collection 为 OpenAPI 格式。"""
    openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": data.get("info", {}).get("name", "API"),
            "version": "1.0.0",
        },
        "paths": {},
    }

    def process_items(items):
        for item in items:
            if "item" in item:
                # 子文件夹
                process_items(item["item"])
            elif "request" in item:
                request = item["request"]
                method = request.get("method", "GET").lower()
                url = request.get("url", {})

                if isinstance(url, str):
                    path = url
                else:
                    path_parts = url.get("path", [])
                    path = "/" + "/".join(path_parts)

                if path not in openapi["paths"]:
                    openapi["paths"][path] = {}

                openapi["paths"][path][method] = {
                    "summary": item.get("name", ""),
                    "tags": [item.get("name", "").split("/")[0] if "/" in item.get("name", "") else "default"],
                }

    items = data.get("item", [])
    process_items(items)

    return openapi


def _convert_rap_to_openapi(data: dict) -> dict:
    """转换 RAP / YAPI 格式为 OpenAPI。"""
    openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": data.get("data", {}).get("name", "API"),
            "version": "1.0.0",
        },
        "paths": {},
    }

    interfaces = data.get("data", {}).get("interfaces", [])
    for iface in interfaces:
        path = iface.get("url", "")
        method = iface.get("method", "GET").lower()

        if path not in openapi["paths"]:
            openapi["paths"][path] = {}

        openapi["paths"][path][method] = {
            "summary": iface.get("name", ""),
            "tags": [iface.get("module", {}).get("name", "default")],
        }

    return openapi


def _build_openapi_from_apis(apis: list) -> dict:
    """从 API 列表构建 OpenAPI 格式。"""
    openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": "API",
            "version": "1.0.0",
        },
        "paths": {},
    }

    for api in apis:
        path = api.get("path", "")
        method = api.get("method", "GET").lower()

        if path not in openapi["paths"]:
            openapi["paths"][path] = {}

        openapi["paths"][path][method] = {
            "summary": api.get("summary", ""),
            "tags": api.get("tags", ["default"]),
        }

    return openapi


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


def _save_summary(summary: dict, api_dir: Path):
    """保存摘要。"""
    # 保存为 YAML
    with open(api_dir / "endpoints_summary.yaml", "w", encoding="utf-8") as f:
        yaml.dump(summary, f, allow_unicode=True, default_flow_style=False)

    # 显示摘要
    _show_api_summary(summary)


def _show_api_summary(summary: dict):
    """显示 API 摘要。"""
    table = Table(title="API 端点摘要")

    table.add_column("分组", style="bold")
    table.add_column("端点数", justify="right")

    for group, count in summary.get("groups", {}).items():
        table.add_row(group, str(count))

    table.add_row("[bold]总计[/bold]", f"[bold]{summary.get('total_endpoints', 0)}[/bold]")

    console.print(table)


# 需要导入 Prompt 和 Confirm
from rich.prompt import Prompt, Confirm
