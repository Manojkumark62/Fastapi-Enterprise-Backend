from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from models.otp import OTP
from models.refresh_token import RefreshToken
from models.session import UserSession


def cleanup_expired_security_records(db: Session) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    otp_result = db.execute(delete(OTP).where(OTP.expires_at < now))
    token_result = db.execute(delete(RefreshToken).where(RefreshToken.expires_at < now))
    session_result = db.execute(delete(UserSession).where(UserSession.expires_at < now))
    db.commit()
    return {
        "otps": otp_result.rowcount or 0,
        "refresh_tokens": token_result.rowcount or 0,
        "sessions": session_result.rowcount or 0,
    }