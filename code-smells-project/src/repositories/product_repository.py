from src.database import get_db
from src.models import Product


class ProductRepository:
    def __init__(self, connection_factory=get_db):
        self.connection_factory = connection_factory

    @staticmethod
    def _map(row):
        return Product(**dict(row)) if row else None

    def list_all(self):
        rows = self.connection_factory().execute("SELECT * FROM produtos ORDER BY id").fetchall()
        return [self._map(row) for row in rows]

    def get(self, product_id):
        row = self.connection_factory().execute(
            "SELECT * FROM produtos WHERE id = ?", (product_id,)
        ).fetchone()
        return self._map(row)

    def create(self, data):
        db = self.connection_factory()
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (data["nome"], data["descricao"], data["preco"], data["estoque"], data["categoria"]),
        )
        db.commit()
        return cursor.lastrowid

    def update(self, product_id, data):
        db = self.connection_factory()
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (data["nome"], data["descricao"], data["preco"], data["estoque"], data["categoria"], product_id),
        )
        db.commit()

    def delete(self, product_id):
        db = self.connection_factory()
        db.execute("DELETE FROM produtos WHERE id = ?", (product_id,))
        db.commit()

    def search(self, term="", category=None, minimum=None, maximum=None):
        clauses = ["1 = 1"]
        params = []
        if term:
            clauses.append("(nome LIKE ? OR descricao LIKE ?)")
            value = f"%{term}%"
            params.extend([value, value])
        if category:
            clauses.append("categoria = ?")
            params.append(category)
        if minimum is not None:
            clauses.append("preco >= ?")
            params.append(minimum)
        if maximum is not None:
            clauses.append("preco <= ?")
            params.append(maximum)
        rows = self.connection_factory().execute(
            f"SELECT * FROM produtos WHERE {' AND '.join(clauses)} ORDER BY id", params
        ).fetchall()
        return [self._map(row) for row in rows]
