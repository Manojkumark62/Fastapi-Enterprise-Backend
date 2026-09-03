"""
Authentication service — registration, login, token issuance/refresh, logout.

Design decisions worth calling out:
- Login failures are tracked per-user in `login_attempts` and checked
  against MAX_LOGIN_ATTEMPTS / ACCOUNT_LOCK_DURATION_MINUTES (Module 28).
  The lock is computed from recent attempt history, not a stored
  "locked_until" column — this means a lock naturally expires without
  needing a background job to clear it.
- Refresh tokens are rotated on every use: the old one is revoked and a
  new one issued. This limits the blast radius if a refresh token is
  ever stolen — it's single-use in practice.
- Every public method here raises the custom exceptions from
  exceptions/custom_exceptions.py rather than HTTPException, so this
  service has zero FastAPI import and is fully unit-testable in
  isolation (see tests/unit/test_auth_service.py in a later pass).
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.constants import ACCOUNT_LOCK_DURATION_MINUTES, MAX_LOGIN_ATTEMPTS, OTP_EXPIRE_MINUTES, OTP_LENGTH
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from exceptions.custom_exceptions import (
    AccountInactiveError,
    AccountLockedError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenRevokedError,
)
from models.login_attempt import LoginAttempt
from models.refresh_token import RefreshToken
from models.otp import OTP
from models.user import User
from models.session import UserSession
from schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from services.email_service import send_password_reset_code
from services.role_service import RoleService
from jose import JWTError


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    # ----------------------------------------------------------------
    # Registration
    # ----------------------------------------------------------------

    def register(self, payload: UserRegisterRequest) -> User:
        existing = self.db.execute(
            select(User).where(User.email == payload.email)
        ).scalar_one_or_none()

        if existing is not None:
            raise EmailAlreadyRegisteredError()

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise EmailAlreadyRegisteredError() from exc
        self.db.refresh(user)

        RoleService(self.db).assign_default_user_role(user.id)
        return user

    def request_password_reset(self, email: str) -> None:
        user = self.db.scalar(select(User).where(User.email == email, User.is_deleted.is_(False)))
        if user is None:
            return
        code = f"{__import__('secrets').randbelow(10 ** OTP_LENGTH):0{OTP_LENGTH}d}"
        otp = OTP(user_id=user.id, code_hash=hash_password(code), purpose="password_reset",
                  expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES))
        self.db.add(otp)
        self.db.commit()
        send_password_reset_code(str(user.email), code)

    def confirm_password_reset(self, email: str, code: str, new_password: str) -> None:
        user = self.db.scalar(select(User).where(User.email == email, User.is_deleted.is_(False)))
        if user is None:
            raise InvalidTokenError("Invalid or expired reset code")
        otp = self.db.scalar(select(OTP).where(OTP.user_id == user.id, OTP.purpose == "password_reset",
                                               OTP.is_used.is_(False)).order_by(OTP.id.desc()))
        if otp is None or otp.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) or otp.attempt_count >= 5:
            raise InvalidTokenError("Invalid or expired reset code")
        otp.attempt_count += 1
        if not verify_password(code, otp.code_hash):
            self.db.commit()
            raise InvalidTokenError("Invalid or expired reset code")
        user.hashed_password = hash_password(new_password)
        otp.is_used = True
        now = datetime.now(timezone.utc)
        self.db.query(UserSession).filter(UserSession.user_id == user.id).update(
            {UserSession.is_active: False, UserSession.last_active_at: now}
        )
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id, RefreshToken.is_revoked.is_(False)
        ).update({RefreshToken.is_revoked: True, RefreshToken.revoked_at: now})
        self.db.commit()

    # ----------------------------------------------------------------
    # Login
    # ----------------------------------------------------------------

    def _is_account_locked(self, user: User) -> bool:
        """
        Locked if there have been >= MAX_LOGIN_ATTEMPTS consecutive failed
        attempts within the lock window, with no successful attempt since.
        Computed from history rather than a stored flag, so the lock
        expires on its own once the window passes.
        """
        window_start = datetime.now(timezone.utc) - timedelta(minutes=ACCOUNT_LOCK_DURATION_MINUTES)

        recent_attempts = self.db.execute(
            select(LoginAttempt)
            .where(LoginAttempt.user_id == user.id)
            .where(LoginAttempt.attempted_at >= window_start)
            .order_by(LoginAttempt.attempted_at.desc())
        ).scalars().all()

        consecutive_failures = 0
        for attempt in recent_attempts:
            if attempt.was_successful:
                break
            consecutive_failures += 1

        return consecutive_failures >= MAX_LOGIN_ATTEMPTS

    def _record_login_attempt(
        self, user: User, was_successful: bool, ip_address: str | None = None
    ) -> None:
        attempt = LoginAttempt(
            user_id=user.id,
            was_successful=was_successful,
            ip_address=ip_address,
            attempted_at=datetime.now(timezone.utc),
        )
        self.db.add(attempt)
        self.db.commit()

    def login(
        self,
        payload: UserLoginRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        user = self.db.execute(
            select(User).where(User.email == payload.email, User.is_deleted.is_(False))
        ).scalar_one_or_none()

        # Deliberately raise the same InvalidCredentialsError whether the
        # email doesn't exist or the password is wrong — distinguishing
        # the two in the response would let an attacker enumerate
        # registered emails.
        if user is None:
            raise InvalidCredentialsError()

        if self._is_account_locked(user):
            raise AccountLockedError()

        if not verify_password(payload.password, user.hashed_password):
            self._record_login_attempt(user, was_successful=False, ip_address=ip_address)
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountInactiveError()

        self._record_login_attempt(user, was_successful=True, ip_address=ip_address)

        user.last_login_at = datetime.now(timezone.utc)
        self.db.commit()

        return self._issue_token_pair(user, ip_address=ip_address, user_agent=user_agent)

    # ----------------------------------------------------------------
    # Token issuance / refresh
    # ----------------------------------------------------------------

    def _issue_token_pair(
        self,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
    ) -> TokenResponse:
        if session_id is None:
            session_id = str(__import__("uuid").uuid4())
            session_expires_at = datetime.now(timezone.utc) + timedelta(
                days=__import__("core.config", fromlist=["settings"]).settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
            self.db.add(UserSession(
                user_id=user.id,
                session_token=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=session_expires_at,
                last_active_at=datetime.now(timezone.utc),
            ))
        access_token = create_access_token(subject=str(user.id), extra_claims={"sid": session_id})
        refresh_token_str = create_refresh_token(subject=str(user.id), extra_claims={"sid": session_id})

        # Decode to pull the jti we just embedded, so we can store it for
        # future revocation lookups without re-deriving it.
        payload = decode_token(refresh_token_str)

        refresh_token_row = RefreshToken(
            user_id=user.id,
            token_jti=payload["jti"],
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            is_revoked=False,
        )
        self.db.add(refresh_token_row)
        self.db.commit()

        return TokenResponse(access_token=access_token, refresh_token=refresh_token_str)

    def refresh_access_token(self, refresh_token_str: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token_str)
        except JWTError:
            raise InvalidTokenError()

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Provided token is not a refresh token")

        token_jti = payload.get("jti")
        subject = payload.get("sub")
        if not isinstance(token_jti, str) or not isinstance(subject, str):
            raise InvalidTokenError()
        try:
            subject_id = int(subject)
        except ValueError as exc:
            raise InvalidTokenError() from exc

        token_row = self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.token_jti == token_jti)
            .with_for_update()
        ).scalar_one_or_none()

        if token_row is None:
            raise InvalidTokenError()

        if token_row.is_revoked:
            raise TokenRevokedError()

        stored_expiry = token_row.expires_at
        if stored_expiry.tzinfo is None:
            # Some DB drivers (SQLite in particular) return naive datetimes
            # even from a DateTime(timezone=True) column. Everything we
            # write is UTC (see _issue_token_pair), so it's safe to assume
            # UTC here rather than raise on the comparison below.
            stored_expiry = stored_expiry.replace(tzinfo=timezone.utc)

        if stored_expiry < datetime.now(timezone.utc):
            raise InvalidTokenError("Refresh token has expired")

        if token_row.user_id != subject_id:
            raise InvalidTokenError()

        user = self.db.get(User, token_row.user_id)
        if user is None or not user.is_active or user.is_deleted:
            raise AccountInactiveError()

        # Rotate: revoke the token just used, issue a brand new pair.
        token_row.is_revoked = True
        token_row.revoked_at = datetime.now(timezone.utc)
        self.db.commit()

        session_id = payload.get("sid")
        if not isinstance(session_id, str):
            raise InvalidTokenError()
        session = self.db.scalar(
            select(UserSession).where(UserSession.session_token == session_id)
        )
        if session is None or not session.is_active:
            raise TokenRevokedError()
        session_expiry = session.expires_at
        if session_expiry.tzinfo is None:
            session_expiry = session_expiry.replace(tzinfo=timezone.utc)
        if session_expiry <= datetime.now(timezone.utc):
            raise InvalidTokenError("Session has expired")
        return self._issue_token_pair(
            user,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            session_id=session.session_token,
        )

    # ----------------------------------------------------------------
    # Logout
    # ----------------------------------------------------------------

    def logout(self, refresh_token_str: str) -> None:
        """Revoke a single refresh token (logout this device only)."""
        payload_or_none = None
        try:
            payload_or_none = decode_token(refresh_token_str)
        except JWTError:
            # Already invalid/expired — nothing to revoke, treat as success.
            return

        token_jti = payload_or_none.get("jti")
        if not isinstance(token_jti, str):
            return
        token_row = self.db.execute(
            select(RefreshToken).where(RefreshToken.token_jti == token_jti)
        ).scalar_one_or_none()

        if token_row is not None and not token_row.is_revoked:
            token_row.is_revoked = True
            token_row.revoked_at = datetime.now(timezone.utc)
            session_id = payload_or_none.get("sid")
            if isinstance(session_id, str):
                self.db.query(UserSession).filter(
                    UserSession.session_token == session_id
                ).update({UserSession.is_active: False})
            self.db.commit()

    def logout_all_devices(self, user_id: int) -> int:
        """
        Revoke every active refresh token for a user (Module 30).
        Returns the number of tokens revoked.
        """
        active_tokens = self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.is_revoked == False)  # noqa: E712 — SQLAlchemy needs == here, not `is`
        ).scalars().all()

        now = datetime.now(timezone.utc)
        for token in active_tokens:
            token.is_revoked = True
            token.revoked_at = now

        self.db.query(UserSession).filter(
            UserSession.user_id == user_id, UserSession.is_active.is_(True)
        ).update({UserSession.is_active: False, UserSession.last_active_at: now})

        self.db.commit()
        return len(active_tokens)
