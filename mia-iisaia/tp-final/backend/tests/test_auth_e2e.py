import os

import httpx
import pytest

BACKEND_URL = os.environ.get("E2E_BACKEND_URL", "http://localhost:8000")
KEYCLOAK_URL = os.environ.get("E2E_KEYCLOAK_URL", "http://localhost:8080")
REALM = "expense-app"
TEST_CLIENT_ID = "expense-test"


def _stack_is_up() -> bool:
    try:
        return httpx.get(f"{BACKEND_URL}/health", timeout=2.0).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _stack_is_up(),
    reason="E2E requires the full Docker stack running (docker compose up)",
)


def _get_token(username: str, password: str) -> str:
    response = httpx.post(
        f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": TEST_CLIENT_ID,
            "username": username,
            "password": password,
        },
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def test_me_with_valid_token_returns_user():
    token = _get_token("alice", "alice123")
    response = httpx.get(
        f"{BACKEND_URL}/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10.0,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["keycloak_sub"]


def test_me_without_token_is_unauthorized():
    response = httpx.get(f"{BACKEND_URL}/api/v1/users/me", timeout=10.0)
    assert response.status_code == 401


def test_cors_preflight_succeeds_without_token():
    # Proves CORS is the outermost middleware: preflight is answered without auth.
    response = httpx.options(
        f"{BACKEND_URL}/api/v1/users/me",
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "GET",
        },
        timeout=10.0,
    )
    assert response.status_code in (200, 204)
    header_names = {k.lower() for k in response.headers}
    assert "access-control-allow-origin" in header_names
