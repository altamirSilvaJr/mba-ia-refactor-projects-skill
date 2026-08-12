# Guidelines da arquitetura MVC alvo

## Objetivo

Aplicar separação de responsabilidades sem forçar uma árvore idêntica em todas as tecnologias. Preservar convenções idiomáticas do framework quando elas cumprem os mesmos limites.

## Fluxo permitido

```text
HTTP → View/Route → Controller → Service/Use Case → Model/Repository → Database
                         ↓                 ↓
                       DTOs          gateways externos
```

Dependências apontam para dentro ou para abstrações. O composition root conecta implementações concretas.

## Responsabilidades

### Views/Routes

- Declarar método, path, middleware e binding do request.
- Converter entrada HTTP em DTO e saída do controller em resposta.
- Não conter SQL, acesso direto ao ORM, cálculos de domínio ou workflows.
- Preservar endpoints, status e formatos existentes, exceto exposição insegura documentada.

### Controllers

- Orquestrar um caso de uso e traduzir resultados/erros para o contrato da aplicação.
- Depender de services/use cases, não de conexão global ou detalhes do framework de banco.
- Permanecer pequenos; não acumular regras extensas de preço, estoque, autenticação ou relatório.

### Models

- Representar entidades, value objects e invariantes de domínio.
- Não conhecer request/response, `jsonify`, Express `req/res` ou templates HTTP.
- Models ORM podem mapear persistência quando idiomático, mas queries complexas ficam em repositories.

### Services/Use Cases

- Coordenar regras que atravessam entidades, transações, gateways e notificações.
- Expor operações orientadas a intenção, como `checkout`, `create_order` ou `assign_task`.
- Não formatar HTTP.

### Repositories

- Encapsular queries, ORM e persistência.
- Oferecer operações orientadas ao domínio, parametrizadas e testáveis.
- Não decidir status HTTP ou regras de apresentação.

### Config

- Ler ambiente e validar configuração no boot.
- Manter defaults apenas quando seguros para desenvolvimento.
- Nunca versionar segredos; mascará-los em logs.

### Middlewares/Error handlers

- Centralizar autenticação, autorização, correlação, logging e tradução de erros inesperados.
- Não esconder exceções sem registro adequado.

### Composition root

- Criar app, configuração, banco, repositories, services e controllers.
- Registrar routes/blueprints/routers.
- Ser o único lugar autorizado a conhecer a maioria das implementações concretas.

## Estruturas de referência

### Python/Flask

```text
src/
├── app.py
├── config/settings.py
├── models/
├── repositories/
├── services/
├── controllers/
├── views/routes/
└── middlewares/error_handler.py
```

Usar factory `create_app()` quando viável. Blueprints pertencem a views/routes; extensão de banco é inicializada no composition root.

### Node.js/Express

```text
src/
├── app.js
├── server.js
├── config/
├── models/
├── repositories/
├── services/
├── controllers/
├── routes/
└── middlewares/errorHandler.js
```

Separar construção do app de `listen()` para permitir testes sem abrir porta.

## Restrições de migração

- Não renomear rotas, campos ou códigos de status silenciosamente.
- Não trocar framework ou banco apenas para “melhorar” arquitetura.
- Não criar camadas vazias que apenas repassam chamada sem estabelecer limite útil.
- Manter transações no nível do caso de uso.
- Introduzir compatibilidade temporária quando uma migração grande exigir etapas.
- Adicionar testes de caracterização antes de alterar comportamento não documentado.

## Critérios de aceite arquitetural

- Entry point/composition root claro.
- Configuração isolada e sem segredos hardcoded.
- Routes sem persistência ou regra de negócio pesada.
- Controllers separados por domínio/caso de uso.
- Models não dependem do protocolo HTTP.
- Persistência parametrizada e encapsulada.
- Erros centralizados.
- Dependências externas substituíveis em testes.
- Boot e contrato original validados.
