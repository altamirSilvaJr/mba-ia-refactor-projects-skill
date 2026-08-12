import re
import sqlite3

from src.services.errors import ApplicationError


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class UserService:
    def __init__(self, repository):
        self.repository = repository

    def list_all(self):
        return [user.to_dict() for user in self.repository.list_all()]

    def get(self, user_id):
        user = self.repository.get(user_id)
        if not user:
            raise ApplicationError("Usuário não encontrado", 404)
        return user.to_dict()

    def create(self, payload):
        if not isinstance(payload, dict):
            raise ApplicationError("Dados inválidos")
        name = str(payload.get("nome", "")).strip()
        email = str(payload.get("email", "")).strip().lower()
        password = payload.get("senha", "")
        if not name or not email or not password:
            raise ApplicationError("Nome, email e senha são obrigatórios")
        if not EMAIL_PATTERN.match(email):
            raise ApplicationError("Email inválido")
        if not isinstance(password, str) or len(password) < 8:
            raise ApplicationError("Senha deve ter no mínimo 8 caracteres")
        try:
            return self.repository.create(name, email, password)
        except sqlite3.IntegrityError as error:
            raise ApplicationError("Email já cadastrado", 409) from error

    def login(self, payload):
        if not isinstance(payload, dict):
            raise ApplicationError("Dados inválidos")
        email, password = payload.get("email", ""), payload.get("senha", "")
        if not email or not password:
            raise ApplicationError("Email e senha são obrigatórios")
        user = self.repository.authenticate(email, password)
        if not user:
            raise ApplicationError("Email ou senha inválidos", 401)
        return user.to_dict()
