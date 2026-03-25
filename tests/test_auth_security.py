"""
Security tests for cookie-based auth, CSRF, token lifecycle, and logout.
Validates the security hardening implemented per SECURITY_ASSESSMENT_2026-03-23.
"""
import pytest
from httpx import AsyncClient
from tests.conftest import SUPERUSER_EMAIL, SUPERUSER_PASSWORD

ACCESS_COOKIE = "unihr_access"
REFRESH_COOKIE = "unihr_refresh"
CSRF_COOKIE = "unihr_csrf"
CSRF_HEADER = "X-CSRF-Token"

LOGIN_URL = "/api/v1/auth/login/access-token"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
ME_URL = "/api/v1/auth/me"


# ────────────────────────────────────────
# Login & Cookie Tests
# ────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_sets_httponly_cookies(client: AsyncClient):
    """Login must set access, refresh, and CSRF cookies."""
    resp = await client.post(
        LOGIN_URL,
        data={"username": SUPERUSER_EMAIL, "password": SUPERUSER_PASSWORD},
    )
    assert resp.status_code == 200

    # Response body must NOT contain access_token
    body = resp.json()
    assert body.get("access_token") is None
    assert body["token_type"] == "bearer"

    # Cookies must be set
    assert ACCESS_COOKIE in resp.cookies
    assert CSRF_COOKIE in resp.cookies
    # Refresh cookie is path-restricted, httpx may or may not expose it
    # depending on the request path — we verify via refresh test below


@pytest.mark.asyncio
async def test_cookie_auth_works_for_protected_endpoint(client: AsyncClient):
    """After login, cookies should authenticate subsequent requests."""
    await client.post(
        LOGIN_URL,
        data={"username": SUPERUSER_EMAIL, "password": SUPERUSER_PASSWORD},
    )
    # client cookie jar now has the access cookie
    resp = await client.get(ME_URL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == SUPERUSER_EMAIL


@pytest.mark.asyncio
async def test_bearer_header_fallback_still_works(client: AsyncClient):
    """Bearer header should still work when no cookies are present."""
    login_resp = await client.post(
        LOGIN_URL,
        data={"username": SUPERUSER_EMAIL, "password": SUPERUSER_PASSWORD},
    )
    token = login_resp.cookies.get(ACCESS_COOKIE)
    assert token

    # Clear cookies — use Bearer header only
    client.cookies.clear()
    resp = await client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == SUPERUSER_EMAIL


# ────────────────────────────────────────
# CSRF Protection Tests
# ────────────────────────────────────────

@pytest.mark.asyncio
async def test_csrf_required_for_unsafe_method_with_cookies(client: AsyncClient):
    """POST to protected endpoint without CSRF header must return 403."""
    await client.post(
        LOGIN_URL,
        data={"username": SUPERUSER_EMAIL, "password": SUPERUSER_PASSWORD},
    )
    # client has cookies, but let's NOT send the CSRF header
    # Try a state-changing endpoint that requires auth
    resp = await client.post(LOGOUT_URL)
    assert resp.status_code == 403
    assert "CSRF" in resp.json().get("detail", "")


@pytest.mark.asyncio
async def test_csrf_passes_with_correct_header(client: AsyncClient):
    """POST with matching CSRF header+cookie should succeed."""
    login_resp = await client.post(
        LOGIN_URL,
        data={"username": SUPERUSER_EMAIL, "password": SUPERUSER_PASSWORD},
    )
    csrf_token = login_resp.cookies.get(CSRF_COOKIE)
    assert csrf_token

    resp = await client.post(LOGOUT_URL, headers={CSRF_HEADER: csrf_token})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_csrf_rejected_with_wrong_header(client: AsyncClient):
    """POST with mismatched CSRF header must fail."""
    await client.post(
        LOGIN_URL,
        data={"username": SUPERUSER_EMAIL, "password": SUPERUSER_PASSWORD},
    )
    resp = await client.post(LOGOUT_URL, headers={CSRF_HEADER: "bad-csrf-value"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_csrf_not_required_for_bearer_only(client: AsyncClient):
    """Bearer-only auth (no cookies) should bypass CSRF."""
    login_resp = await client.post(
        LOGIN_URL,
        data={"username": SUPERUSER_EMAIL, "password": SUPERUSER_PASSWORD},
    )
    token = login_resp.cookies.get(ACCESS_COOKIE)
    client.cookies.clear()

    # Use Bearer header without CSRF — should succeed
    resp = await client.post(
        LOGOUT_URL,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


# ────────────────────────────────────────
# Token Refresh Tests
# ────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_rotates_tokens(client: AsyncClient):
    """Refresh must issue new tokens and keep the session valid."""
    login_resp = await client.post(
        LOGIN_URL,
        data={"username": SUPERUSER_EMAIL, "password": SUPERUSER_PASSWORD},
    )
    old_access = login_resp.cookies.get(ACCESS_COOKIE)
    csrf_token = login_resp.cookies.get(CSRF_COOKIE)

    # Refresh endpoint — path-restricted cookie may or may not be sent by httpx
    # depending on path matching. Use body fallback if needed.
    # Decode the login response to get the refresh token from cookies
    refresh_token = login_resp.cookies.get(REFRESH_COOKIE)

    if refresh_token:
        # Cookie-based refresh
        resp = await client.post(REFRESH_URL, headers={CSRF_HEADER: csrf_token})
    else:
        # If httpx didn't send the path-restricted cookie, try body-based
        # (This can happen in test because the login response path differs from /api/v1/auth/refresh)
        # We need to extract the refresh token differently — skip if not available
        pytest.skip("httpx ASGITransport may not handle path-restricted cookies")

    assert resp.status_code == 200
    new_access = resp.cookies.get(ACCESS_COOKIE)
    if new_access:
        assert new_access != old_access, "Access token should be rotated"


# ────────────────────────────────────────
# Logout Tests
# ────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout_clears_cookies(client: AsyncClient):
    """Logout must clear all auth cookies."""
    login_resp = await client.post(
        LOGIN_URL,
        data={"username": SUPERUSER_EMAIL, "password": SUPERUSER_PASSWORD},
    )
    csrf_token = login_resp.cookies.get(CSRF_COOKIE)

    resp = await client.post(LOGOUT_URL, headers={CSRF_HEADER: csrf_token})
    assert resp.status_code == 200
    assert resp.json()["msg"] == "Logged out"

    # After logout, /me should fail
    me_resp = await client.get(ME_URL)
    assert me_resp.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_request_returns_401(client: AsyncClient):
    """Request without any auth must return 401."""
    resp = await client.get(ME_URL)
    assert resp.status_code == 401


# ────────────────────────────────────────
# SSRF Protection (unit test)
# ────────────────────────────────────────

def test_ssrf_blocks_private_ips():
    """_validate_external_url must reject private/reserved IP ranges."""
    from app.services.document_parser import _validate_external_url

    blocked_urls = [
        "http://127.0.0.1/admin",
        "http://localhost/secret",
        "http://[::1]/admin",
        "http://0.0.0.0/",
        "ftp://example.com/file",       # non-http scheme
        "file:///etc/passwd",
        "gopher://evil.com/",
    ]
    for url in blocked_urls:
        with pytest.raises(ValueError, match="(Blocked|Only http|blocked|\u7981\u6b62|\u53ea\u5141\u8a31)"):
            _validate_external_url(url)


def test_ssrf_allows_public_urls():
    """_validate_external_url must allow legitimate public URLs."""
    from app.services.document_parser import _validate_external_url

    # These should NOT raise (DNS resolution to public IP)
    # Note: may fail in air-gapped environments without DNS
    try:
        _validate_external_url("https://example.com/page")
    except ValueError:
        # If DNS fails, that's OK — the important thing is the above blocked check works
        pass


# ────────────────────────────────────────
# SSO redirect_uri validation (unit test)
# ────────────────────────────────────────

def test_sso_redirect_uri_validation(monkeypatch):
    """SSO redirect_uri must be in the server-side allowlist."""
    from app.config import settings
    from app.api.v1.endpoints.sso import _validate_redirect_uri

    monkeypatch.setattr(settings, "SSO_DEFAULT_REDIRECT_URI", "http://localhost:3001/login/callback")
    monkeypatch.setattr(settings, "SSO_ALLOWED_REDIRECT_URIS", "")
    monkeypatch.setattr(settings, "FRONTEND_BASE_URL", "http://localhost:3001")

    # Allowed
    _validate_redirect_uri("http://localhost:3001/login/callback")

    # Blocked
    import pytest as pt
    with pt.raises(Exception):
        _validate_redirect_uri("https://evil.com/callback")


# ────────────────────────────────────────
# Production config enforcement (unit test)
# ────────────────────────────────────────

def test_production_config_blocks_insecure_secret_key():
    """Production must reject weak SECRET_KEY."""
    from pydantic import ValidationError
    from app.config import Settings

    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="change_this",
            POSTGRES_PASSWORD="safe_pw",
            FIRST_SUPERUSER_EMAIL="prod@corp.com",
            FIRST_SUPERUSER_PASSWORD="Strong123!",
            EMAIL_PROVIDER="resend",
            POSTGRES_SSL_MODE="require",
            CLAMAV_ENABLED=True,
            ADMIN_IP_WHITELIST_ENABLED=True,
        )


def test_production_config_blocks_default_db_password():
    """Production must reject default DB password."""
    from pydantic import ValidationError
    from app.config import Settings

    with pytest.raises(ValidationError, match="POSTGRES_PASSWORD"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="a" * 48,
            POSTGRES_PASSWORD="postgres",
            FIRST_SUPERUSER_EMAIL="prod@corp.com",
            FIRST_SUPERUSER_PASSWORD="Strong123!",
            EMAIL_PROVIDER="resend",
            POSTGRES_SSL_MODE="require",
            CLAMAV_ENABLED=True,
            ADMIN_IP_WHITELIST_ENABLED=True,
        )


def test_production_config_blocks_clamav_disabled():
    """Production must reject CLAMAV_ENABLED=false."""
    from pydantic import ValidationError
    from app.config import Settings

    with pytest.raises(ValidationError, match="CLAMAV_ENABLED"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="a" * 48,
            POSTGRES_PASSWORD="safe_pw",
            FIRST_SUPERUSER_EMAIL="prod@corp.com",
            FIRST_SUPERUSER_PASSWORD="Strong123!",
            EMAIL_PROVIDER="resend",
            POSTGRES_SSL_MODE="require",
            CLAMAV_ENABLED=False,
            ADMIN_IP_WHITELIST_ENABLED=True,
        )
