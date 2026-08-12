from sqlalchemy import func, select

from database import db
from models.category import Category
from models.task import Task


class CategoryRepository:
    def all_with_task_counts(self):
        statement = (
            select(Category, func.count(Task.id))
            .outerjoin(Task, Task.category_id == Category.id)
            .group_by(Category.id)
        )
        return db.session.execute(statement).all()

    def get(self, category_id):
        return db.session.get(Category, category_id)

    def save(self, category):
        db.session.add(category)

    def delete_preserving_tasks(self, category):
        db.session.execute(
            Task.__table__.update()
            .where(Task.category_id == category.id)
            .values(category_id=None)
        )
        db.session.delete(category)

