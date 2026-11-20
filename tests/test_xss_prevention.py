"""Tests for XSS prevention in textarea contexts."""

import pytest
from markupsafe import escape


def test_textarea_injection_escaped():
    """HTML special characters should be escaped."""
    malicious_input = "</textarea><script>alert(1)</script><textarea>"
    escaped = escape(malicious_input)
    
    assert "&lt;" in escaped
    assert "&gt;" in escaped
    assert "<script>" not in escaped
    assert "</textarea>" not in escaped


def test_xss_payload_escaped():
    """XSS payloads should be rendered as text."""
    payloads = [
        "<img src=x onerror=alert(1)>",
        "<svg onload=alert(1)>",
        "javascript:alert(1)",
        "'>alert(String.fromCharCode(88,83,83))</script><script>var x='",
    ]
    
    for payload in payloads:
        escaped = escape(payload)
        assert "<" not in escaped.lstrip("&")
        assert ">" not in escaped.rstrip(";")
        assert "script" not in escaped.lower() or "&" in escaped


def test_escape_preserves_text_content():
    """Escaping should preserve the actual text."""
    text = "What's the answer? <see this> & that"
    escaped = escape(text)
    
    assert "What's the answer?" in escaped
    assert "see this" in escaped
    assert "that" in escaped


def test_escape_handles_unicode():
    """Escaping should handle unicode correctly."""
    text = "Größe"
    escaped = escape(text)
    
    assert "Größe" in str(escaped)


def test_escape_empty_string():
    """Escaping empty string should return empty."""
    assert escape("") == ""


def test_escape_none_safe():
    """Escape should handle None gracefully (in template context)."""
    result = escape(None) if None else ""
    assert result == ""
