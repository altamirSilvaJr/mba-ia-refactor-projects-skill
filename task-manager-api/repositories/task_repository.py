from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task


class TaskRepository:
    def all_with_relations(self):
        statement = select(Task).options(joinedload(Task.user), joinedload(Task.category))
        return list(db.session.scalars(statement).unique())

    def get(self, task_id):
        return db.session.get(Task, task_id)

    def for_user(self, user_id):
        return list(db.session.scalars(select(Task).where(Task.user_id == user_id)))

    def search(self, query="", status="", priority=None, user_id=None):
        statement = select(Task)
        if query:
            statement = statement.where(
                or_(Task.title.like(f"%{query}%"), Task.description.like(f"%{query}%"))
            )
        if status:
            statement = statement.where(Task.status == status)
        if priority is not None:
            statement = statement.where(Task.priority == priority)
        if user_id is not None:
            statement = statement.where(Task.user_id == user_id)
        return list(db.session.scalars(statement))

    def counts(self):
        rows = db.session.execute(
            select(Task.status, func.count(Task.id)).group_by(Task.status)
        ).all()
        result = {status: count for status, count in rows}
        result["total"] = sum(result.values())
        return result

    def save(self, task):
        db.session.add(task)

    def delete(self, task):
        db.session.delete(task)

