"""Automatic audit and record-history capture for ORM mutations."""

import json
from contextvars import ContextVar

from sqlalchemy import event
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from models.audit_log import AuditLog
from models.record_history import RecordHistory

_current_actor_id: ContextVar[int | None] = ContextVar("audit_actor_id", default=None)


def set_audit_actor(actor_id: int | None) -> None:
    _current_actor_id.set(actor_id)


def _snapshot(entity: object) -> dict:
    state = sa_inspect(entity)
    sensitive = {"hashed_password", "token_jti", "session_token", "code_hash"}
    return {
        attribute.key: value
        for attribute in state.mapper.column_attrs
        if attribute.key not in sensitive
        for value in [getattr(entity, attribute.key)]
    }


@event.listens_for(Session, "after_flush")
def capture_mutations(session: Session, _flush_context) -> None:
    ignored = {AuditLog, RecordHistory}
    entities = list(session.new) + list(session.dirty) + list(session.deleted)
    for entity in entities:
        if type(entity) in ignored or not hasattr(entity, "id") or entity.id is None:
            continue
        state = sa_inspect(entity)
        if entity in session.new:
            change_type = "created"
        elif entity in session.deleted:
            change_type = "deleted"
        elif state.modified:
            change_type = "updated"
        else:
            continue
        actor_id = _current_actor_id.get()
        entity_type = type(entity).__name__
        session.add(RecordHistory(
            entity_type=entity_type,
            entity_id=entity.id,
            snapshot=json.dumps(_snapshot(entity), default=str),
            change_type=change_type,
            changed_by_id=actor_id,
        ))
        session.add(AuditLog(
            actor_id=actor_id,
            action=f"{entity_type.upper()}_{change_type.upper()}",
            entity_type=entity_type,
            entity_id=entity.id,
        ))
