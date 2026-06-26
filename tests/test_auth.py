import os

os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _make_mock_client():
    mock_user = MagicMock()
    mock_user.id = "test-user-id"
    mock_user.email = "user@example.com"
    mock_user.created_at = "2024-01-01T00:00:00Z"
    mock_user.app_metadata = {}
    mock_user.user_metadata = {}

    mock_session = MagicMock()
    mock_session.access_token = "mock-access-token"
    mock_session.refresh_token = "mock-refresh-token"
    mock_session.expires_in = 3600
    mock_session.expires_at = 1700000000
    mock_session.user = mock_user

    mock_response = MagicMock()
    mock_response.user = mock_user
    mock_response.session = mock_session

    mock_auth = MagicMock()
    mock_auth.sign_up.return_value = mock_response
    mock_auth.sign_in_with_password.return_value = mock_response
    mock_auth.refresh_session.return_value = mock_response
    mock_auth.get_user.return_value = mock_response
    mock_auth.sign_out.return_value = None

    mock_client = MagicMock()
    mock_client.auth = mock_auth
    return mock_client


@patch("app.db.supabase_client._supabase_client", None)
@patch("app.db.supabase_client.create_client")
def test_signup(mock_create_client):
    mock_create_client.return_value = _make_mock_client()
    from app.main import create_app
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "user@example.com", "password": "hunter2"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["access_token"] == "mock-access-token"
    assert data["refresh_token"] == "mock-refresh-token"
    assert data["token_type"] == "bearer"


@patch("app.db.supabase_client._supabase_client", None)
@patch("app.db.supabase_client.create_client")
def test_login(mock_create_client):
    mock_create_client.return_value = _make_mock_client()
    from app.main import create_app
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "hunter2"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "mock-access-token"


@patch("app.db.supabase_client._supabase_client", None)
@patch("app.db.supabase_client.create_client")
def test_refresh_token(mock_create_client):
    mock_create_client.return_value = _make_mock_client()
    from app.main import create_app
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "mock-refresh-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "mock-access-token"


@patch("app.db.supabase_client._supabase_client", None)
@patch("app.db.supabase_client.create_client")
def test_me(mock_create_client):
    mock_create_client.return_value = _make_mock_client()
    from app.main import create_app
    client = TestClient(create_app())
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer mock-access-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"


@patch("app.db.supabase_client._supabase_client", None)
@patch("app.db.supabase_client.create_client")
def test_me_unauthorized(mock_create_client):
    mock_create_client.return_value = _make_mock_client()
    from app.main import create_app
    client = TestClient(create_app())
    response = client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)
