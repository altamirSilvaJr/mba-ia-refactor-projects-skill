class ReportService:
    def __init__(self, repository):
        self.repository = repository

    def sales(self):
        row = self.repository.sales()
        revenue = row["faturamento"]
        discount = revenue * (0.1 if revenue > 10000 else 0.05 if revenue > 5000 else 0.02 if revenue > 1000 else 0)
        total = row["total_pedidos"]
        return {
            "total_pedidos": total,
            "faturamento_bruto": round(revenue, 2),
            "desconto_aplicavel": round(discount, 2),
            "faturamento_liquido": round(revenue - discount, 2),
            "pedidos_pendentes": row["pendentes"],
            "pedidos_aprovados": row["aprovados"],
            "pedidos_cancelados": row["cancelados"],
            "ticket_medio": round(revenue / total, 2) if total else 0,
        }

    def health(self):
        return self.repository.counts()
