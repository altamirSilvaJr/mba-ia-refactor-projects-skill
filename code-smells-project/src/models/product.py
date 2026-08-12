from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Product:
    id: int
    nome: str
    descricao: str
    preco: float
    estoque: int
    categoria: str
    ativo: int
    criado_em: str

    def to_dict(self):
        return asdict(self)
