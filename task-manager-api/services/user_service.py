from database import db
from errors import ApplicationError
from models.user import User
from services.validators import VALID_ROLES, require_json_object, validate_email


class UserService:
    def __init__(self, users, tasks, token_issuer):
        self.users = users
        self.tasks = tasks
        self.token_issuer = token_issuer

    def list_users(self):
        return [dict(user.to_dict(), task_count=len(user.tasks)) for user in self.users.all_with_tasks()]

    def get_user(self, user_id):
        user = self._get(user_id)
        data = user.to_dict()
        data["tasks"] = [task.to_dict() for task in self.tasks.for_user(user_id)]
        return data

    def create_user(self, data, allow_privileged_role=False):
        data = require_json_object(data)
        name, email, password = data.get("name"), data.get("email"), data.get("password")
        if not name:
            raise ApplicationError("Nome é obrigatório", 400)
        if not email:
            raise ApplicationError("Email é obrigatório", 400)
        if not password:
            raise ApplicationError("Senha é obrigatória", 400)
        validate_email(email)
        if len(password) < 4:
            raise ApplicationError("Senha deve ter no mínimo 4 caracteres", 400)
        if self.users.by_email(email):
            raise ApplicationError("Email já cadastrado", 409)
        role = data.get("role", "user") if allow_privileged_role else "user"
        if role not in VALID_ROLES:
            raise ApplicationError("Role inválido", 400)
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        self._commit_new(user)
        return user.to_dict()

    def update_user(self, user_id, data, can_change_role=False):
        user = self._get(user_id)
        data = require_json_object(data)
        if "name" in data:
            user.name = data["name"]
        if "email" in data:
            validate_email(data["email"])
            existing = self.users.by_email(data["email"])
            if existing and existing.id != user_id:
                raise ApplicationError("Email já cadastrado", 409)
            user.email = data["email"]
        if "password" in data:
            if not isinstance(data["password"], str) or len(data["password"]) < 4:
                raise ApplicationError("Senha muito curta", 400)
            user.set_password(data["password"])
        if "role" in data:
            if not can_change_role:
                raise ApplicationError("Acesso negado", 403)
            if data["role"] not in VALID_ROLES:
                raise ApplicationError("Role inválido", 400)
            user.role = data["role"]
        if "active" in data:
            user.active = bool(data["active"])
        self._commit()
        return user.to_dict()

    def delete_user(self, user_id):
        user = self._get(user_id)
        try:
            for task in self.tasks.for_user(user_id):
                self.tasks.delete(task)
            self.users.delete(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return {"message": "Usuário deletado com sucesso"}

    def user_tasks(self, user_id):
        self._get(user_id)
        result = []
        for task in self.tasks.for_user(user_id):
            data = task.to_dict()
            data.pop("user_id", None)
            data.pop("category_id", None)
            data.pop("updated_at", None)
            data.pop("tags", None)
            data["overdue"] = task.is_overdue()
            result.append(data)
        return result

    def login(self, data):
        data = require_json_object(data)
        email, password = data.get("email"), data.get("password")
        if not email or not password:
            raise ApplicationError("Email e senha são obrigatórios", 400)
        user = self.users.by_email(email)
        if not user or not user.check_password(password):
            raise ApplicationError("Credenciais inválidas", 401)
        if not user.active:
            raise ApplicationError("Usuário inativo", 403)
        self._commit()  # Persiste eventual upgrade de hash MD5.
        return {
            "message": "Login realizado com sucesso",
            "user": user.to_dict(),
            "token": self.token_issuer(user),
        }

    def _get(self, user_id):
        user = self.users.get(user_id)
        if not user:
            raise ApplicationError("Usuário não encontrado", 404)
        return user

    def _commit_new(self, user):
        try:
            self.users.save(user)
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

