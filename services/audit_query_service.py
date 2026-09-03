"""Advanced audit logging query and filtering (Modules 56-57)."""

from datetime import datetime
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models.audit_log import AuditLog
from models.record_history import RecordHistory


class AuditQueryService:
    """Advanced querying of audit logs and record history."""

    @staticmethod
    def list_audit_logs_advanced(
        db: Session,
        actor_id: int | None = None,
        entity_type: str | None = None,
        action: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """
        List audit logs with advanced filtering.
        
        Returns:
            Tuple of (audit_logs, total_count)
        """
        query = db.query(AuditLog)
        
        if actor_id is not None:
            query = query.filter(AuditLog.actor_id == actor_id)
        
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
        
        return logs, total

    @staticmethod
    def list_entity_history(
        db: Session,
        entity_type: str,
        entity_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[RecordHistory], int]:
        """
        List change history for a specific entity.
        
        Returns:
            Tuple of (history_records, total_count)
        """
        query = db.query(RecordHistory).filter(
            and_(
                RecordHistory.entity_type == entity_type,
                RecordHistory.entity_id == entity_id,
            )
        )
        
        total = query.count()
        history = query.order_by(RecordHistory.created_at.desc()).offset(skip).limit(limit).all()
        
        return history, total

    @staticmethod
    def get_entity_timeline(
        db: Session,
        entity_type: str,
        entity_id: int,
    ) -> list[dict]:
        """
        Get a complete timeline of all changes to an entity.
        
        Returns:
            List of dicts with change history including who, what, when
        """
        history = db.query(RecordHistory).filter(
            and_(
                RecordHistory.entity_type == entity_type,
                RecordHistory.entity_id == entity_id,
            )
        ).order_by(RecordHistory.created_at.asc()).all()
        
        timeline = []
        for record in history:
            timeline.append({
                "timestamp": record.created_at.isoformat(),
                "change_type": record.change_type,
                "changed_by_id": record.changed_by_id,
                "snapshot": record.snapshot,
            })
        
        return timeline
