from werkzeug.security import check_password_hash, generate_password_hash

from src.database import get_db
from src.models import User


class UserRepository:
    def __init__(self, connection_factory=get_db):
        self.connection_factory = connection_factory

    @staticmethod
    def _map(row):
        if not row:
            return None
        return User(row["id"], row["nome"], row["email"], row["tipo"], row["criado_em"])

    def list_all(self):
        rows = self.connection_factory().execute(
            "SELECT id, nome, email, tipo, criado_em FROM usuarios ORDER BY id"
        ).fetchall()
        return [self._map(row) for row in rows]

    def get(self, user_id):
        row = self.connection_factory().execute(
            "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?", (user_id,)
        ).fetchone()
        return self._map(row)

    def create(self, name, email, password, role="cliente"):
        db = self.connection_factory()
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (name, email, generate_password_hash(password), role),
        )
        db.commit()
        return cursor.lastrowid

    def authenticate(self, email, password):
        row = self.connection_factory().execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        if not row or not check_password_hash(row["senha"], password):
            return None
        return self._map(row)
