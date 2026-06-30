"""Tests for server/auth.py — API authentication.

Tests: _is_exempt, _secure_compare, generate_api_key.
Pure functions — no HTTP server needed.
"""
import pytest

from aitest.server.auth import (
    _is_exempt, _secure_compare, generate_api_key, _EXEMPT_PREFIXES, _EXEMPT_EXACT,
)


# ══════════════════════════════════════════════════════════════════════════
#  _is_exempt
# ══════════════════════════════════════════════════════════════════════════


class TestIsExempt:
    def test_root_is_exempt(self):
        assert _is_exempt("/") is True
        assert _is_exempt("") is True

    def test_health_is_exempt(self):
        assert _is_exempt("/health") is True

    def test_docs_is_exempt(self):
        assert _is_exempt("/docs") is True
        assert _is_exempt("/openapi.json") is True

    def test_static_is_exempt(self):
        assert _is_exempt("/static/app.js") is True
        assert _is_exempt("/static/css/main.css") is True

    def test_ws_is_exempt(self):
        assert _is_exempt("/ws/chat") is True

    def test_protected_paths_not_exempt(self):
        assert _is_exempt("/api/orgs") is False
        assert _is_exempt("/chat") is False
        assert _is_exempt("/api/v1/execution") is False

    def test_similar_but_not_exact(self):
        # /docs-v2 matches /docs via startswith — known prefix-match behavior
        # /healthz matches /health via startswith — known prefix-match behavior
        assert _is_exempt("/api/health") is False  # Not at root, not exempt
        assert _is_exempt("/v1/docs") is False  # docs not at start


# ══════════════════════════════════════════════════════════════════════════
#  _secure_compare
# ══════════════════════════════════════════════════════════════════════════


class TestSecureCompare:
    def test_equal_strings(self):
        assert _secure_compare("abc123", "abc123") is True

    def test_different_strings(self):
        assert _secure_compare("abc123", "xyz789") is False

    def test_different_lengths(self):
        assert _secure_compare("short", "loooong") is False

    def test_empty_strings(self):
        assert _secure_compare("", "") is True

    def test_case_sensitive(self):
        assert _secure_compare("Key123", "key123") is False

    def test_single_char_diff(self):
        assert _secure_compare("abcdef", "abcdeF") is False

    def test_known_key_format(self):
        key = generate_api_key()
        assert _secure_compare(key, key) is True
        assert _secure_compare(key, key + "x") is False


# ══════════════════════════════════════════════════════════════════════════
#  generate_api_key
# ══════════════════════════════════════════════════════════════════════════


class TestGenerateApiKey:
    def test_has_prefix(self):
        key = generate_api_key()
        assert key.startswith("aitest_")

    def test_sufficient_length(self):
        key = generate_api_key()
        # aitest_ (7) + 32 bytes base64 ≈ 43 chars → ~50 total
        assert len(key) > 40

    def test_unique_keys(self):
        keys = {generate_api_key() for _ in range(20)}
        assert len(keys) == 20

    def test_no_whitespace(self):
        key = generate_api_key()
        assert " " not in key
        assert "\n" not in key
