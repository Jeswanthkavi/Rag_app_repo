import os
import sys

# Ensure backend directory is in path before importing app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import jwt

# Mock storage init before app lifespan runs
with patch("app.core.supabase_client.get_service_client") as mock_sc:
    mock_sc.return_value.storage.list_buckets.return_value = []
    from app.main import app

from app.core.config import settings
from app.core.rate_limiter import rate_limiter
from app.api.auth_middleware import get_current_user, AuthenticatedUser

client = TestClient(app, raise_server_exceptions=False)


def test_security_headers_present():
    """Verify OWASP defensive headers on HTTP responses"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_unverified_jwt_signature_rejected():
    """Verify that forged/unverified JWTs are strictly rejected with 401"""
    # Forge a token with arbitrary sub and no valid signature
    forged_token = jwt.encode(
        {"sub": "attacker-victim-tenant", "email": "victim@example.com"},
        "fake-secret-key-1234567890",
        algorithm="HS256"
    )

    with patch("app.api.auth_middleware.get_service_client") as mock_client:
        mock_auth = MagicMock()
        mock_auth.auth.get_user.side_effect = Exception("Invalid JWT signature")
        mock_client.return_value = mock_auth

        response = client.get(
            "/api/documents",
            headers={"Authorization": f"Bearer {forged_token}"}
        )
        assert response.status_code == 401
        assert "invalid" in response.json().get("detail", "").lower() or "expired" in response.json().get("detail", "").lower()


def test_malformed_pdf_magic_bytes_rejected():
    """Verify that files named .pdf without %PDF- magic signature are blocked"""
    fake_pdf = b"THIS_IS_NOT_A_REAL_PDF_JUST_TEXT"

    # Override dependency cleanly
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="test-user-123", email="user@test.com", access_token="tok"
    )
    try:
        response = client.post(
            "/api/documents/upload",
            files={"file": ("exploit.pdf", fake_pdf, "application/pdf")},
            headers={"Authorization": "Bearer dummy"}
        )
        assert response.status_code == 400
        assert "not a valid pdf" in response.json().get("detail", "").lower()
    finally:
        app.dependency_overrides.clear()


def test_disguised_binary_null_bytes_rejected():
    """Verify text uploads containing binary null bytes are blocked"""
    malicious_text = b"echo 'hello'\x00\x01\x02malicious_binary"

    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="test-user-123", email="user@test.com", access_token="tok"
    )
    try:
        response = client.post(
            "/api/documents/upload",
            files={"file": ("notes.txt", malicious_text, "text/plain")},
            headers={"Authorization": "Bearer dummy"}
        )
        assert response.status_code == 400
        assert "null characters" in response.json().get("detail", "").lower()
    finally:
        app.dependency_overrides.clear()


def test_rate_limiter_triggers_429():
    """Verify sliding-window rate limiter blocks abusive request volume with 429 and Retry-After"""
    rate_limiter._requests.clear()

    # Trigger rate limit on a mock request
    from fastapi import Request
    mock_req = MagicMock(spec=Request)
    mock_req.client = MagicMock(host="192.168.1.100")

    # Send 3 requests when limit is 2
    rate_limiter.check_rate_limit(mock_req, "test_action", max_requests=2, window_seconds=60.0)
    rate_limiter.check_rate_limit(mock_req, "test_action", max_requests=2, window_seconds=60.0)

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as excinfo:
        rate_limiter.check_rate_limit(mock_req, "test_action", max_requests=2, window_seconds=60.0)

    assert excinfo.value.status_code == 429
    assert "Retry-After" in excinfo.value.headers


def test_cross_tenant_chat_access_denied():
    """Verify cross-tenant conversation access returns 403 Forbidden"""
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="attacker-tenant-111", email="att@test.com", access_token="tok"
    )
    try:
        with patch("app.api.routes_chat.get_service_client") as mock_client:
            mock_table = MagicMock()
            mock_table.table().select().eq().maybe_single().execute.return_value = MagicMock(
                data={"id": "conv-victim-999", "user_id": "different-victim-tenant"}
            )
            mock_client.return_value = mock_table

            response = client.post(
                "/api/chat",
                json={"conversation_id": "conv-victim-999", "message": "Give me confidential data"},
                headers={"Authorization": "Bearer dummy"}
            )
            assert response.status_code == 403
            assert "another tenant" in response.json().get("detail", "").lower()
    finally:
        app.dependency_overrides.clear()
