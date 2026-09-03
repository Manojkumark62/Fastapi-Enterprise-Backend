"""Auth endpoints — wraps AuthService (Pass 3) for HTTP consumption."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from dependencies.auth import get_current_user, get_current_active_user
from dependencies.db import get_db
from exceptions.custom_exceptions import (
    AccountInactiveError,
    AccountLockedError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenRevokedError,
)
from models.user import User
from schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    UserRegisterRequest,
)
from schemas.common import MessageResponse
from schemas.user import UserResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        return service.register(payload)
    except EmailAlreadyRegisteredError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, request: Request, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        return service.login(payload, ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))
    except AccountLockedError as e:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=e.message)
    except AccountInactiveError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)


@router.post("/token", response_model=TokenResponse)
def token(form: OAuth2PasswordRequestForm = Depends(), request: Request = None, db: Session = Depends(get_db)):
    service = AuthService(db)
    payload = UserLoginRequest(email=form.username, password=form.password)
    try:
        return service.login(payload, ip_address=request.client.host if request and request.client else None, user_agent=request.headers.get("user-agent") if request else None)
    except AccountLockedError as e:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=e.message)
    except AccountInactiveError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        return service.refresh_access_token(payload.refresh_token)
    except TokenRevokedError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)
    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)
    except AccountInactiveError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    AuthService(db).request_password_reset(str(payload.email))
    return MessageResponse(message="If the account exists, a reset code has been sent")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)):
    try:
        AuthService(db).confirm_password_reset(str(payload.email), payload.code, payload.new_password)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return MessageResponse(message="Password reset successfully")


@router.post("/logout", response_model=MessageResponse)
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.logout(payload.refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponse)
def logout_all(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    service = AuthService(db)
    count = service.logout_all_devices(current_user.id)
    return MessageResponse(message=f"Logged out from {count} device(s)")


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_active_user)):
    return current_user
