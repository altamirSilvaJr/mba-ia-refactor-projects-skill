from src.database import get_db
from src.models import Order, OrderItem


class OrderRepository:
    def __init__(self, connection_factory=get_db):
        self.connection_factory = connection_factory

    def create(self, user_id, items):
        db = self.connection_factory()
        try:
            user = db.execute("SELECT id FROM usuarios WHERE id = ?", (user_id,)).fetchone()
            if not user:
                raise ValueError("Usuário não encontrado")
            product_ids = [item["produto_id"] for item in items]
            placeholders = ",".join("?" for _ in product_ids)
            products = db.execute(
                f"SELECT id, nome, preco, estoque FROM produtos WHERE id IN ({placeholders})",
                product_ids,
            ).fetchall()
            by_id = {row["id"]: row for row in products}
            total = 0
            for item in items:
                product = by_id.get(item["produto_id"])
                if not product:
                    raise ValueError(f"Produto {item['produto_id']} não encontrado")
                if product["estoque"] < item["quantidade"]:
                    raise ValueError(f"Estoque insuficiente para {product['nome']}")
                total += product["preco"] * item["quantidade"]
            cursor = db.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                (user_id, total),
            )
            order_id = cursor.lastrowid
            for item in items:
                product = by_id[item["produto_id"]]
                db.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (order_id, product["id"], item["quantidade"], product["preco"]),
                )
                db.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                    (item["quantidade"], product["id"]),
                )
            db.commit()
            return {"pedido_id": order_id, "total": total}
        except Exception:
            db.rollback()
            raise

    def list_all(self, user_id=None):
        where = "WHERE p.usuario_id = ?" if user_id is not None else ""
        params = (user_id,) if user_id is not None else ()
        rows = self.connection_factory().execute(f"""
            SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
                   i.produto_id, pr.nome AS produto_nome, i.quantidade, i.preco_unitario
            FROM pedidos p
            LEFT JOIN itens_pedido i ON i.pedido_id = p.id
            LEFT JOIN produtos pr ON pr.id = i.produto_id
            {where}
            ORDER BY p.id, i.id
        """, params).fetchall()
        orders = {}
        for row in rows:
            order = orders.setdefault(row["id"], Order(
                row["id"], row["usuario_id"], row["status"], row["total"], row["criado_em"]
            ))
            if row["produto_id"] is not None:
                order.itens.append(OrderItem(
                    row["produto_id"], row["produto_nome"], row["quantidade"], row["preco_unitario"]
                ))
        return list(orders.values())

    def update_status(self, order_id, status):
        db = self.connection_factory()
        cursor = db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, order_id))
        db.commit()
        return cursor.rowcount > 0
