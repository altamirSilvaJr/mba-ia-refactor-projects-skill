from src.services.errors import ApplicationError


class AdminService:
    def __init__(self, connection_factory, configured_token):
        self.connection_factory = connection_factory
        self.configured_token = configured_token

    def reset(self, supplied_token):
        if not self.configured_token or supplied_token != self.configured_token:
            raise ApplicationError("Operação administrativa não autorizada", 403)
        db = self.connection_factory()
        try:
            for table in ("itens_pedido", "pedidos", "produtos", "usuarios"):
                db.execute(f"DELETE FROM {table}")
            db.commit()
        except Exception:
            db.rollback()
            raise
