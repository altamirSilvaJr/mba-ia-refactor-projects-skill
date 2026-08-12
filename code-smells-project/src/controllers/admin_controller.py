class AdminController:
    def __init__(self, service): self.service = service
    def reset(self, token):
        self.service.reset(token)
        return {"mensagem": "Banco de dados resetado", "sucesso": True}, 200
    @staticmethod
    def query_disabled():
        return {"erro": "Execução de SQL remoto foi desativada", "sucesso": False}, 410
