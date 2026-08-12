class OrderController:
    def __init__(self, service): self.service = service
    def create(self, data):
        return {"dados": self.service.create(data), "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201
    def list_all(self): return {"dados": self.service.list_all(), "sucesso": True}, 200
    def list_for_user(self, user_id): return {"dados": self.service.list_for_user(user_id), "sucesso": True}, 200
    def update_status(self, order_id, data):
        self.service.update_status(order_id, data.get("status", "") if isinstance(data, dict) else "")
        return {"sucesso": True, "mensagem": "Status atualizado"}, 200
