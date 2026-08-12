from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class OrderItem:
    produto_id: int
    produto_nome: str
    quantidade: int
    preco_unitario: float


@dataclass
class Order:
    id: int
    usuario_id: int
    status: str
    total: float
    criado_em: str
    itens: list[OrderItem] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
