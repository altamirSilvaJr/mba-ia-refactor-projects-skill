class ProductController:
    def __init__(self, service): self.service = service
    def list_all(self): return {"dados": self.service.list_all(), "sucesso": True}, 200
    def get(self, product_id): return {"dados": self.service.get(product_id), "sucesso": True}, 200
    def create(self, data):
        product_id = self.service.create(data)
        return {"dados": {"id": product_id}, "sucesso": True, "mensagem": "Produto criado"}, 201
    def update(self, product_id, data):
        self.service.update(product_id, data)
        return {"sucesso": True, "mensagem": "Produto atualizado"}, 200
    def delete(self, product_id):
        self.service.delete(product_id)
        return {"sucesso": True, "mensagem": "Produto deletado"}, 200
    def search(self, args):
        items = self.service.search(args.get("q", ""), args.get("categoria"), args.get("preco_min"), args.get("preco_max"))
        return {"dados": items, "total": len(items), "sucesso": True}, 200
