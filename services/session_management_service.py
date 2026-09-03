"""Session management service for active user sessions (Module 30)."""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.session import UserSession
from exceptions.custom_exceptions import AppException


class SessionManagementService:
    """Manage active user sessions."""

    @staticmethod
    def list_active_sessions(db: Session, user_id: int) -> list[UserSession]:
        """List all active sessions for a user."""
        now = datetime.now(timezone.utc)
        return (
            db.query(UserSession)
            .filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,
                    UserSession.expires_at > now,
                )
            )
            .all()
        )

    @staticmethod
    def get_session(db: Session, session_id: int, user_id: int) -> UserSession:
        """Get a specific session belonging to a user."""
        session = (
            db.query(UserSession)
            .filter(UserSession.id == session_id, UserSession.user_id == user_id)
            .first()
        )
        if not session:
            raise AppException("Session not found")
        return session

    @staticmethod
    def revoke_session(db: Session, session_id: int, user_id: int) -> UserSession:
        """Revoke (deactivate) a specific session."""
        session = SessionManagementService.get_session(db, session_id, user_id)
        session.is_active = False
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def revoke_all_sessions_except_current(db: Session, user_id: int, current_session_token: str) -> int:
        """Revoke all sessions except the current one."""
        current = (
            db.query(UserSession)
            .filter(UserSession.session_token == current_session_token)
            .first()
        )
        result = (
            db.query(UserSession)
            .filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.id != (current.id if current else -1),
                )
            )
            .update({UserSession.is_active: False})
        )
        db.commit()
        return result
