from src.services.errors import ApplicationError


VALID_STATUSES = {"pendente", "aprovado", "enviado", "entregue", "cancelado"}


class OrderService:
    def __init__(self, repository):
        self.repository = repository

    def create(self, payload):
        if not isinstance(payload, dict):
            raise ApplicationError("Dados inválidos")
        user_id, items = payload.get("usuario_id"), payload.get("itens")
        if not isinstance(user_id, int) or user_id <= 0:
            raise ApplicationError("Usuario ID é obrigatório")
        if not isinstance(items, list) or not items:
            raise ApplicationError("Pedido deve ter pelo menos 1 item")
        normalized = []
        for item in items:
            if not isinstance(item, dict):
                raise ApplicationError("Item inválido")
            product_id, quantity = item.get("produto_id"), item.get("quantidade")
            if not isinstance(product_id, int) or not isinstance(quantity, int) or quantity <= 0:
                raise ApplicationError("Produto e quantidade devem ser inteiros positivos")
            normalized.append({"produto_id": product_id, "quantidade": quantity})
        try:
            return self.repository.create(user_id, normalized)
        except ValueError as error:
            raise ApplicationError(str(error)) from error

    def list_all(self):
        return [order.to_dict() for order in self.repository.list_all()]

    def list_for_user(self, user_id):
        return [order.to_dict() for order in self.repository.list_all(user_id)]

    def update_status(self, order_id, status):
        if status not in VALID_STATUSES:
            raise ApplicationError("Status inválido")
        if not self.repository.update_status(order_id, status):
            raise ApplicationError("Pedido não encontrado", 404)
