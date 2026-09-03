"""Authentication endpoint contract tests."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from starlette.requests import Request

from core.constants import PermissionCodeEnum
from database.base import Base
from dependencies.permissions import require_permission_or_self
from main import app
from models.user import User
from schemas.auth import UserRegisterRequest
from services.auth_service import AuthService
from services.role_service import RoleService

client = TestClient(app)


def test_auth_register_endpoint_exists():
    """Verify registration endpoint and response schema."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
        },
    )
    # Endpoint exists and returns 201 or 422 (validation)
    assert response.status_code in (201, 422, 409)


def test_auth_login_endpoint_exists():
    """Verify login endpoint."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "SecurePass123!"},
    )
    # Endpoint exists (401 if user not found, 200 if successful)
    assert response.status_code in (200, 401)


def test_auth_forgot_password_endpoint_exists():
    """Verify forgot-password endpoint."""
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "test@example.com"},
    )
    # Endpoint exists and returns generic response
    assert response.status_code in (200, 422)


def test_auth_reset_password_endpoint_exists():
    """Verify reset-password endpoint."""
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"email": "test@example.com", "code": "000000", "new_password": "NewPass123!"},
    )
    # Endpoint exists (returns 400 if invalid code)
    assert response.status_code in (400, 422, 200)


def test_register_assigns_default_user_role_and_allows_role_assignment():
    """A registered user should get a default role, and the role catalog should exist."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        RoleService(db).ensure_default_roles_and_permissions()

        user = AuthService(db).register(
            UserRegisterRequest(
                email="newuser@example.com",
                password="SecurePass123!",
                full_name="New User",
            )
        )

        assert "USER" in RoleService(db).get_user_role_names(user.id)

        RoleService(db).assign_role(user.id, "ADMIN")
        assert RoleService(db).user_has_role(user.id, "ADMIN")


def test_require_permission_or_self_allows_current_user_to_update_their_own_record():
    """Users should be able to edit their own profile without an admin-only permission."""
    request = Request({"type": "http", "method": "PATCH", "headers": []})
    current_user = User(
        id=7,
        email="me@example.com",
        hashed_password="secret",
        full_name="Me",
        is_active=True,
        is_superuser=False,
    )

    dependency = require_permission_or_self(PermissionCodeEnum.UPDATE_USER)
    result = dependency(request=request, user_id=7, current_user=current_user, db=None)

    assert result is current_user
