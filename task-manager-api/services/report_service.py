from datetime import datetime, timedelta

from database import db
from errors import ApplicationError
from models.category import Category
from models.task import Task
from services.validators import require_json_object


class ReportService:
    def __init__(self, tasks, users, categories):
        self.tasks = tasks
        self.users = users
        self.categories = categories

    def summary(self):
        tasks = self.tasks.search()
        users = self.users.all_with_tasks()
        counts = self.tasks.counts()
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        overdue_tasks = [task for task in tasks if task.is_overdue()]
        priorities = {priority: 0 for priority in range(1, 6)}
        for task in tasks:
            priorities[task.priority] = priorities.get(task.priority, 0) + 1
        user_stats = []
        for user in users:
            total = len(user.tasks)
            completed = sum(task.status == "done" for task in user.tasks)
            user_stats.append({
                "user_id": user.id,
                "user_name": user.name,
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": round((completed / total) * 100, 2) if total else 0,
            })
        return {
            "generated_at": str(datetime.utcnow()),
            "overview": {
                "total_tasks": counts.get("total", 0),
                "total_users": len(users),
                "total_categories": len(self.categories.all_with_task_counts()),
            },
            "tasks_by_status": {name: counts.get(name, 0) for name in ("pending", "in_progress", "done", "cancelled")},
            "tasks_by_priority": {
                "critical": priorities[1], "high": priorities[2], "medium": priorities[3],
                "low": priorities[4], "minimal": priorities[5],
            },
            "overdue": {
                "count": len(overdue_tasks),
                "tasks": [{
                    "id": task.id, "title": task.title, "due_date": str(task.due_date),
                    "days_overdue": (datetime.utcnow() - task.due_date).days,
                } for task in overdue_tasks],
            },
            "recent_activity": {
                "tasks_created_last_7_days": sum(task.created_at >= seven_days_ago for task in tasks),
                "tasks_completed_last_7_days": sum(
                    task.status == "done" and task.updated_at >= seven_days_ago for task in tasks
                ),
            },
            "user_productivity": user_stats,
        }

    def user_report(self, user_id):
        user = self.users.get(user_id)
        if not user:
            raise ApplicationError("Usuário não encontrado", 404)
        tasks = self.tasks.for_user(user_id)
        total = len(tasks)
        status_counts = {name: sum(task.status == name for task in tasks) for name in ("done", "pending", "in_progress", "cancelled")}
        return {
            "user": {"id": user.id, "name": user.name, "email": user.email},
            "statistics": dict(
                total_tasks=total,
                **status_counts,
                overdue=sum(task.is_overdue() for task in tasks),
                high_priority=sum(task.priority <= 2 for task in tasks),
                completion_rate=round((status_counts["done"] / total) * 100, 2) if total else 0,
            ),
        }

    def list_categories(self):
        result = []
        for category, task_count in self.categories.all_with_task_counts():
            result.append(dict(category.to_dict(), task_count=task_count))
        return result

    def create_category(self, data):
        data = require_json_object(data)
        name = data.get("name")
        if not name:
            raise ApplicationError("Nome é obrigatório", 400)
        category = Category(name=name, description=data.get("description", ""), color=data.get("color", "#000000"))
        self._save(category)
        return category.to_dict()

    def update_category(self, category_id, data):
        category = self._get_category(category_id)
        data = require_json_object(data)
        for field in ("name", "description", "color"):
            if field in data:
                setattr(category, field, data[field])
        self._commit()
        return category.to_dict()

    def delete_category(self, category_id):
        category = self._get_category(category_id)
        try:
            self.categories.delete_preserving_tasks(category)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return {"message": "Categoria deletada"}

    def _get_category(self, category_id):
        category = self.categories.get(category_id)
        if not category:
            raise ApplicationError("Categoria não encontrada", 404)
        return category

    def _save(self, category):
        try:
            self.categories.save(category)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def _commit():
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

