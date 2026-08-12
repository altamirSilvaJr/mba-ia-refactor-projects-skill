from datetime import datetime

from database import db
from errors import ApplicationError
from models.category import Category
from models.task import Task
from models.user import User
from services.validators import VALID_STATUSES, parse_date, parse_int, require_json_object


class TaskService:
    def __init__(self, tasks, users, categories):
        self.tasks = tasks
        self.users = users
        self.categories = categories

    @staticmethod
    def serialize(task, include_relations=False, include_overdue=False):
        data = task.to_dict()
        if include_overdue:
            data["overdue"] = task.is_overdue()
        if include_relations:
            data["user_name"] = task.user.name if task.user else None
            data["category_name"] = task.category.name if task.category else None
        return data

    def list_tasks(self):
        return [self.serialize(task, True, True) for task in self.tasks.all_with_relations()]

    def get_task(self, task_id):
        task = self._get(task_id)
        return self.serialize(task, include_overdue=True)

    def create_task(self, data):
        values = self._validated_values(require_json_object(data), creating=True)
        task = Task(**values)
        try:
            self.tasks.save(task)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return self.serialize(task)

    def update_task(self, task_id, data):
        task = self._get(task_id)
        values = self._validated_values(require_json_object(data), creating=False)
        for name, value in values.items():
            setattr(task, name, value)
        task.updated_at = datetime.utcnow()
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return self.serialize(task)

    def delete_task(self, task_id):
        task = self._get(task_id)
        try:
            self.tasks.delete(task)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return {"message": "Task deletada com sucesso"}

    def search_tasks(self, args):
        priority = parse_int(args.get("priority"), "Prioridade") if args.get("priority") else None
        user_id = parse_int(args.get("user_id"), "Usuário") if args.get("user_id") else None
        tasks = self.tasks.search(args.get("q", ""), args.get("status", ""), priority, user_id)
        return [self.serialize(task) for task in tasks]

    def stats(self):
        counts = self.tasks.counts()
        all_tasks = self.tasks.search()
        total = counts.pop("total", 0)
        done = counts.get("done", 0)
        return {
            "total": total,
            "pending": counts.get("pending", 0),
            "in_progress": counts.get("in_progress", 0),
            "done": done,
            "cancelled": counts.get("cancelled", 0),
            "overdue": sum(task.is_overdue() for task in all_tasks),
            "completion_rate": round((done / total) * 100, 2) if total else 0,
        }

    def _get(self, task_id):
        task = self.tasks.get(task_id)
        if not task:
            raise ApplicationError("Task não encontrada", 404)
        return task

    def _validated_values(self, data, creating):
        values = {}
        if creating or "title" in data:
            title = data.get("title")
            if not title:
                raise ApplicationError("Título é obrigatório" if creating else "Título muito curto", 400)
            if not isinstance(title, str) or len(title) < 3:
                raise ApplicationError("Título muito curto", 400)
            if len(title) > 200:
                raise ApplicationError("Título muito longo", 400)
            values["title"] = title
        for field in ("description",):
            if field in data or creating:
                values[field] = data.get(field, "")
        if creating or "status" in data:
            status = data.get("status", "pending")
            if status not in VALID_STATUSES:
                raise ApplicationError("Status inválido", 400)
            values["status"] = status
        if creating or "priority" in data:
            priority = parse_int(data.get("priority", 3), "Prioridade")
            if not 1 <= priority <= 5:
                raise ApplicationError("Prioridade deve ser entre 1 e 5", 400)
            values["priority"] = priority
        for field, repository, model, message in (
            ("user_id", self.users, User, "Usuário não encontrado"),
            ("category_id", self.categories, Category, "Categoria não encontrada"),
        ):
            if field in data or creating:
                value = data.get(field)
                if value is not None:
                    value = parse_int(value, field)
                    if not repository.get(value):
                        raise ApplicationError(message, 404)
                values[field] = value
        if "due_date" in data:
            values["due_date"] = parse_date(
                data["due_date"],
                "Formato de data inválido. Use YYYY-MM-DD" if creating else "Formato de data inválido",
            ) if data["due_date"] else None
        if "tags" in data:
            tags = data["tags"]
            values["tags"] = ",".join(str(tag) for tag in tags) if isinstance(tags, list) else tags
        return values

