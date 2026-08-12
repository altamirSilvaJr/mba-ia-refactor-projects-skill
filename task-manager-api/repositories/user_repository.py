from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import db
from models.user import User


class UserRepository:
    def all_with_tasks(self):
        statement = select(User).options(selectinload(User.tasks))
        return list(db.session.scalars(statement))

    def get(self, user_id):
        return db.session.get(User, user_id)

    def by_email(self, email):
        return db.session.scalar(select(User).where(User.email == email))

    def save(self, user):
        db.session.add(user)

    def delete(self, user):
        db.session.delete(user)

