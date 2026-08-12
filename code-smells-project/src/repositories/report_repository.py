from src.database import get_db


class ReportRepository:
    def __init__(self, connection_factory=get_db):
        self.connection_factory = connection_factory

    def sales(self):
        row = self.connection_factory().execute("""
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END) AS pendentes,
                   SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END) AS aprovados,
                   SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelados
            FROM pedidos
        """).fetchone()
        return dict(row)

    def counts(self):
        db = self.connection_factory()
        return {
            table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("produtos", "usuarios", "pedidos")
        }
