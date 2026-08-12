# Guia de validação

## Princípio

Validar comportamento, não apenas estrutura. Uma árvore MVC bonita não comprova funcionamento. Registrar comando, exit code, resultado e limitação. Não instalar dependências sem autorização quando a instalação alterar ambiente ou exigir rede.

## 1. Descobrir a validação existente

Priorizar comandos declarados no projeto:

- Python: `pyproject.toml`, `pytest.ini`, `tox.ini`, `requirements*.txt`, README e scripts.
- Node.js: `package.json` scripts, lockfile e README.
- Endpoints: decorators/routers, OpenAPI, arquivos `.http`, testes e documentação.

Não inventar comando como se fosse fornecido. Quando não houver suíte, criar testes de caracterização proporcionais ao risco ou usar smoke tests reproduzíveis.

## 2. Baseline antes das mudanças

Depois da confirmação da Fase 3 e antes de editar, quando seguro:

1. registrar `git status`;
2. executar testes existentes;
3. iniciar a aplicação com timeout e ambiente de teste;
4. exercitar endpoints representativos;
5. registrar falhas preexistentes.

Não usar banco de produção. Fazer cópia/fixture ou banco temporário quando uma validação puder alterar dados.

## 3. Matriz mínima pós-refatoração

### Estática

- Parse/compile dos arquivos alterados.
- Lint/typecheck existentes.
- Busca por segredos e padrões dos findings originais, sem imprimir valores.
- Conferência de imports e dependências.

### Testes

- Suíte existente completa ou subconjunto justificado.
- Testes de unidade de regras extraídas.
- Testes de integração para repositories/transações.
- Testes de contrato HTTP para endpoints originais.

### Boot real

- Inicializar banco/seed somente pelo procedimento documentado e em ambiente descartável.
- Subir a aplicação em porta livre.
- Aguardar readiness/health com timeout.
- Confirmar ausência de traceback/unhandled rejection.
- Encerrar o processo de forma limpa.

### Endpoints

Cobrir pelo menos:

- health/root quando existentes;
- uma leitura de coleção e uma leitura por ID;
- criação válida e entrada inválida;
- atualização e exclusão em dados descartáveis;
- autenticação/autorização;
- principal caso de negócio, como checkout ou criação de pedido;
- relatório ou endpoint com joins/N+1 corrigido.

Para cada endpoint, comparar método, path, status, content type e shape JSON. Dados dinâmicos podem ser normalizados, mas não ignorados.

## 4. Estratégias por stack

### Flask

- Preferir testes com `app.test_client()` e app factory.
- Para boot, usar o comando documentado ou módulo WSGI com timeout.
- Usar SQLite temporário quando suportado.
- Validar que blueprints foram registrados e que `url_map` preserva endpoints.

### Express

- Separar `createApp()` de `listen()`.
- Preferir o runner já presente; usar cliente HTTP/supertest somente se a dependência existir ou sua adição for autorizada.
- Validar promises rejeitadas, middleware de erro e encerramento do banco/server.

## 5. Reauditoria

Para cada finding original:

- `Corrigido`: causa removida e teste/evidência confirma.
- `Mitigado`: risco reduzido, mas há trabalho residual descrito.
- `Aceito`: mantido por decisão explícita, com justificativa.
- `Bloqueado`: não validável/corrigível por dependência externa ou decisão pendente.

Executar novamente todo o catálogo, incluindo deprecations. Novos findings introduzidos pela refatoração devem ser adicionados, não ocultados.

## 6. Critério de conclusão

Só declarar sucesso completo quando:

- testes relevantes passam;
- aplicação inicia sem erro;
- endpoints originais respondem conforme contrato;
- findings CRITICAL/HIGH planejados foram corrigidos ou explicitamente bloqueados/aceitos;
- relatório contém evidências e limitações;
- nenhuma mudança preexistente do usuário foi perdida.

Se boot ou endpoints não puderem ser executados, usar `BLOCKED`, registrar motivo e não declarar que a aplicação continua funcionando.
