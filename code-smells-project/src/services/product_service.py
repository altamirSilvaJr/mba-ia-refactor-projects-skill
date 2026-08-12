from src.services.errors import ApplicationError


VALID_CATEGORIES = {"informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"}


class ProductService:
    def __init__(self, repository):
        self.repository = repository

    def list_all(self):
        return [product.to_dict() for product in self.repository.list_all()]

    def get(self, product_id):
        product = self.repository.get(product_id)
        if not product:
            raise ApplicationError("Produto não encontrado", 404)
        return product.to_dict()

    def create(self, payload):
        data = self._validate(payload)
        return self.repository.create(data)

    def update(self, product_id, payload):
        self.get(product_id)
        self.repository.update(product_id, self._validate(payload))

    def delete(self, product_id):
        self.get(product_id)
        try:
            self.repository.delete(product_id)
        except Exception as error:
            raise ApplicationError("Produto possui pedidos associados", 409) from error

    def search(self, term, category, minimum, maximum):
        try:
            minimum = float(minimum) if minimum not in (None, "") else None
            maximum = float(maximum) if maximum not in (None, "") else None
        except (TypeError, ValueError) as error:
            raise ApplicationError("Faixa de preço inválida") from error
        if category and category not in VALID_CATEGORIES:
            raise ApplicationError("Categoria inválida")
        return [item.to_dict() for item in self.repository.search(term, category, minimum, maximum)]

    @staticmethod
    def _validate(payload):
        if not isinstance(payload, dict):
            raise ApplicationError("Dados inválidos")
        missing = [name for name in ("nome", "preco", "estoque") if name not in payload]
        if missing:
            labels = {"nome": "Nome", "preco": "Preço", "estoque": "Estoque"}
            raise ApplicationError(f"{labels[missing[0]]} é obrigatório")
        name = payload["nome"]
        if not isinstance(name, str) or len(name.strip()) < 2 or len(name.strip()) > 200:
            raise ApplicationError("Nome deve ter entre 2 e 200 caracteres")
        try:
            price = float(payload["preco"])
            stock = int(payload["estoque"])
        except (TypeError, ValueError) as error:
            raise ApplicationError("Preço e estoque devem ser numéricos") from error
        if price < 0 or stock < 0:
            raise ApplicationError("Preço e estoque não podem ser negativos")
        category = payload.get("categoria", "geral")
        if category not in VALID_CATEGORIES:
            raise ApplicationError("Categoria inválida")
        return {
            "nome": name.strip(), "descricao": str(payload.get("descricao", "")),
            "preco": price, "estoque": stock, "categoria": category,
        }
