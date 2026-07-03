"""API Converters — conversion functions for API formats.

Extracted from api_import.py for single-responsibility.
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


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


