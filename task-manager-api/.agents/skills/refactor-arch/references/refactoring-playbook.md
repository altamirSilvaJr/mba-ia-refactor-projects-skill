# Playbook de refatoração

## Como usar

Selecionar apenas transformações justificadas pelos findings. Adaptar sintaxe à stack detectada, preservar o contrato externo e testar após cada transformação. Os exemplos são mínimos e ilustram o limite arquitetural, não uma biblioteca obrigatória.

## 1. SQL concatenado → query parametrizada

Antes (Python):

```python
cursor.execute("SELECT * FROM users WHERE email = '" + email + "'")
```

Depois:

```python
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
```

Aplicar a todo valor; em filtros dinâmicos, concatenar somente cláusulas fixas e acumular parâmetros separadamente.

## 2. Segredo hardcoded → configuração validada

Antes (JavaScript):

```js
const paymentKey = "pk_live_secret";
```

Depois:

```js
const paymentKey = process.env.PAYMENT_GATEWAY_KEY;
if (!paymentKey) throw new Error("PAYMENT_GATEWAY_KEY is required");
```

Fornecer `.env.example` apenas com nomes/placeholders. Recomendar rotação do segredo exposto.

## 3. Senha insegura → password hasher

Antes (Python):

```python
self.password = hashlib.md5(raw.encode()).hexdigest()
```

Depois:

```python
from werkzeug.security import generate_password_hash
self.password_hash = generate_password_hash(raw)
```

Separar verificação, impedir serialização e definir estratégia de migração para hashes existentes.

## 4. Route com regra → route + controller + service

Antes (Express):

```js
router.post("/checkout", async (req, res) => {
  const course = await db.get(req.body.courseId);
  const payment = await gateway.charge(req.body.card, course.price);
  await db.enroll(req.body.userId, course.id, payment.id);
  res.json({ ok: true });
});
```

Depois:

```js
router.post("/checkout", checkoutController.execute);

class CheckoutController {
  constructor(checkout) { this.checkout = checkout; }
  execute = async (req, res, next) => {
    try { res.json(await this.checkout.execute(req.body)); }
    catch (error) { next(error); }
  };
}
```

O service `checkout` coordena curso, pagamento e matrícula sem depender de `req`/`res`.

## 5. God Module → módulos verticais por domínio

Antes:

```text
controllers.py  # produtos + usuários + pedidos + relatórios
models.py       # todas as queries e regras
```

Depois:

```text
controllers/product_controller.py
controllers/order_controller.py
services/order_service.py
repositories/product_repository.py
repositories/order_repository.py
views/routes/product_routes.py
views/routes/order_routes.py
```

Extrair uma fatia por vez e manter adapters temporários quando necessário para preservar imports.

## 6. Escritas parciais → transação no caso de uso

Antes (pseudocódigo):

```python
order_id = orders.insert(order)
payments.insert(order_id, payment)
stock.decrement(items)
```

Depois:

```python
with unit_of_work.transaction():
    order_id = orders.insert(order)
    payments.insert(order_id, payment)
    stock.decrement(items)
```

Rollback deve cobrir todas as escritas obrigatórias; efeitos externos precisam de idempotência/outbox quando aplicável.

## 7. N+1 → join, eager loading ou lote

Antes (Python):

```python
for task in Task.query.all():
    task.user_name = User.query.get(task.user_id).name
```

Depois:

```python
tasks = Task.query.options(joinedload(Task.user)).all()
for task in tasks:
    task.user_name = task.user.name if task.user else None
```

Para relatórios, preferir `JOIN`, `GROUP BY` e agregação no banco. Comparar contagem de queries quando possível.

## 8. Erros dispersos → error handler central

Antes (Flask):

```python
try:
    return jsonify(service.run()), 200
except Exception as exc:
    return jsonify({"error": str(exc)}), 500
```

Depois:

```python
@app.errorhandler(DomainError)
def handle_domain_error(exc):
    return jsonify({"error": exc.public_message}), exc.status_code
```

Controllers deixam exceções conhecidas chegarem ao handler. Erros internos são registrados com contexto, mas detalhes não vazam na resposta.

## 9. Validação duplicada → schema/DTO compartilhado

Antes:

```python
if len(data["title"]) < 3 or len(data["title"]) > 200:
    return {"error": "invalid"}, 400
```

Depois:

```python
command = TaskInput.from_dict(data)
task = task_service.create(command)
```

`TaskInput` valida tipos e formato; invariantes essenciais permanecem no domínio. Reutilizar em create/update com campos opcionais explícitos.

## 10. API legada → substituto suportado

Antes (SQLAlchemy 2.x em estilo legacy):

```python
user = User.query.get(user_id)
```

Depois:

```python
user = db.session.get(User, user_id)
```

Confirmar versão e documentação antes de aplicar. Encapsular a chamada em repository para reduzir futuras migrações.

## 11. Token fictício → autenticação verificável

Antes:

```python
token = "fake-token-" + str(user.id)
```

Depois (interface):

```python
token = token_service.issue(subject=str(user.id), role=user.role)
```

`token_service` usa biblioteca mantida, assinatura, expiração e validação; middleware resolve identidade e autorização. Não implementar criptografia manualmente.

## 12. Entry point acoplado → app factory/composition root

Antes (Express):

```js
const app = express();
app.listen(3000);
```

Depois:

```js
export function createApp(dependencies) {
  const app = express();
  app.use(buildRoutes(dependencies));
  return app;
}
```

`server.js` chama `createApp()` e `listen()`. Testes importam o app sem abrir porta. Em Flask, usar `create_app(config)` com princípio equivalente.

## Ordem segura sugerida

1. Testes de caracterização e inventário do contrato.
2. Configuração/segredos e tratamento de erros.
3. Composition root e interfaces.
4. Routes/controllers por domínio.
5. Services, repositories e transações.
6. Segurança e performance preservando respostas.
7. APIs deprecated, duplicação e legibilidade.
8. Reauditoria, boot e smoke tests.
