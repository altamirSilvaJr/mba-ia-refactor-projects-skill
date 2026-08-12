class UserController:
    def __init__(self, service): self.service = service
    def list_all(self): return {"dados": self.service.list_all(), "sucesso": True}, 200
    def get(self, user_id): return {"dados": self.service.get(user_id), "sucesso": True}, 200
    def create(self, data): return {"dados": {"id": self.service.create(data)}, "sucesso": True}, 201
    def login(self, data):
        return {"dados": self.service.login(data), "sucesso": True, "mensagem": "Login OK"}, 200
