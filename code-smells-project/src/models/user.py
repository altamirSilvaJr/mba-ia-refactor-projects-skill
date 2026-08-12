from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class User:
    id: int
    nome: str
    email: str
    tipo: str
    criado_em: str

    def to_dict(self):
        return asdict(self)
