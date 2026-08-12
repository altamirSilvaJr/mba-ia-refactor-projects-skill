class ReportController:
    def __init__(self, service): self.service = service
    def sales(self): return {"dados": self.service.sales(), "sucesso": True}, 200
    def health(self):
        return {"status": "ok", "database": "connected", "counts": self.service.health(), "versao": "1.0.0"}, 200
