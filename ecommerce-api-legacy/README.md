# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
ADMIN_API_KEY="uma-chave-aleatoria-com-16-ou-mais-caracteres" npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Os endpoints `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem a chave em `X-API-Key` ou `Authorization: Bearer <chave>`. Consulte `.env.example` para as configurações disponíveis.

Para executar os testes sem dependências adicionais:

```bash
npm test
```

Exemplos de requisições estão em `api.http`.
