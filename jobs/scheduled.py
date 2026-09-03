"""Database-backed jobs suitable for cron or an external scheduler."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.constants import TaskStatusEnum
from models.notification import Notification
from models.task import Task


def create_due_task_reminders(db: Session) -> int:
    """Notify assignees about due tasks that are not complete."""
    tasks = db.scalars(select(Task).where(
        Task.due_date <= date.today(),
        Task.assignee_id.is_not(None),
        Task.status.not_in({TaskStatusEnum.DONE.value, TaskStatusEnum.CANCELLED.value}),
        Task.is_deleted.is_(False),
    )).all()
    created = 0
    for task in tasks:
        existing = db.scalar(select(Notification).where(
            Notification.user_id == task.assignee_id,
            Notification.title == "Task due",
            Notification.message == f"Task '{task.title}' is due.",
        ))
        if existing is None:
            db.add(Notification(
                user_id=task.assignee_id,
                title="Task due",
                message=f"Task '{task.title}' is due.",
                notification_type="warning",
            ))
            created += 1
    db.commit()
    return created