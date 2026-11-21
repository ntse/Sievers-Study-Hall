"""Tests for security headers."""


def test_security_headers_present(app):
    """Verify all required security headers are present."""
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Content-Security-Policy" in response.headers
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Strict-Transport-Security" in response.headers


def test_csp_header_content(app):
    """Verify CSP header has correct content."""
    client = app.test_client()
    response = client.get("/")
    csp = response.headers.get("Content-Security-Policy")

    assert csp is not None, "Content-Security-Policy header missing"
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self'" in csp


def test_hsts_header_content(app):
    """Verify HSTS header includes includeSubDomains."""
    client = app.test_client()
    response = client.get("/")
    hsts = response.headers.get("Strict-Transport-Security")

    assert hsts is not None, "Strict-Transport-Security header missing"
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts
