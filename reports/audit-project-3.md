# Relatório de Auditoria Arquitetural — task-manager-api

## Metadados

| Campo | Valor |
|---|---|
| Projeto | `task-manager-api` |
| Stack | Python (versão não declarada) + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 + SQLite |
| Arquitetura observada | Monólito modular/híbrido: Blueprints e models separados por pasta, mas routes acumulam HTTP, regras e persistência |
| Escopo | `app.py`, `database.py`, `seed.py`, `models/`, `routes/`, `services/`, `utils/`, `requirements.txt` e `README.md`; excluídos Git, dependências, caches, builds, bancos binários e arquivos gerados |
| Arquivos analisados | 15 arquivos-fonte Python |
| Linhas aproximadas | 1.158 linhas Python |
| Data | 2026-08-12 |
| Método | Análise estática orientada por evidências |

## Resumo executivo

A aplicação implementa gestão de usuários, tarefas, categorias e relatórios em 22 endpoints Flask. Embora já tenha separação física entre `models/`, `routes/`, `services/` e `utils/`, o fluxo efetivo salta de handlers HTTP diretamente para o ORM. As routes também fazem validação, cálculo, serialização e controle transacional, caracterizando uma arquitetura híbrida com baixo isolamento entre camadas.

O risco imediato é de segurança: os endpoints não possuem autenticação/autorização efetiva, o login emite um token previsível que não é validado e o cliente pode atribuir a si próprio papéis privilegiados. Além disso, hashes de senha são devolvidos por respostas públicas, há material secreto/configuração sensível no código e as senhas usam MD5 sem salt. A prioridade é bloquear exposição e acesso indevido antes de reorganizar a arquitetura.

Também foram confirmados N+1, consultas sem paginação, validações inconsistentes, tratamento genérico de exceções, política de exclusão referencial indefinida e uso da API ORM legada. Não foram executados boot, seed ou testes nesta fase; portanto, os impactos de runtime indicados devem ser confirmados por baseline na Fase 3.

| Severidade | Quantidade |
|---|---:|
| CRITICAL | 2 |
| HIGH | 2 |
| MEDIUM | 7 |
| LOW | 2 |
| **Total** | **13** |

## Arquitetura atual

`app.py` cria e configura globalmente a aplicação, registra três Blueprints e cria tabelas durante a importação. Os Blueprints adaptam HTTP, consultam e alteram o ORM diretamente, validam entradas, calculam relatórios e montam respostas. Os models definem schema e parte pequena das regras/serialização. O único service, de notificação, não está integrado aos casos de uso observados.

```text
HTTP → Flask app/Blueprint route → Flask-SQLAlchemy Model.query/db.session → SQLite
                                  ↘ validação, regra, cálculo e serialização no handler
```

Objetos persistidos confirmados: tabelas `users`, `categories` e `tasks`, com FKs opcionais de tasks para usuários e categorias (`models/user.py:5-14`, `models/category.py:4-11`, `models/task.py:5-21`). Entry point e boot documentados: `python app.py`; carga inicial: `python seed.py`; instalação: `pip install -r requirements.txt` (`README.md:5-13`). Não há comando de teste, lint ou migration documentado.

## Findings

### [CRITICAL] AUD-001 — Autenticação e autorização inexistentes, com token previsível

- **Arquivo e linhas:** `routes/user_routes.py:42-90`, `routes/user_routes.py:92-151`, `routes/user_routes.py:185-211`; `routes/task_routes.py:85-238`; `routes/report_routes.py:167-223`
- **Categoria:** AP-03 — Autenticação ou autorização inexistente/quebrada
- **Evidência:** o login concatena o ID do usuário a um literal para formar o token, e não existe middleware/guard que valide esse token. Rotas públicas permitem criar usuário escolhendo `role`, alterar `role`, excluir usuários e executar todas as mutações de tarefas e categorias.
- **Descrição:** a aplicação possui verificação pontual de credenciais no login, mas não estabelece sessão verificável nem aplica autenticação ou autorização aos recursos.
- **Impacto:** qualquer cliente pode ler e modificar dados, criar um usuário administrador, alterar privilégios e excluir registros; o token emitido não oferece proteção.
- **Recomendação:** implementar autenticação assinada ou sessão segura, middleware obrigatório e autorização por papel/recurso; impedir atribuição arbitrária de papéis na borda pública.
- **Critério de aceite:** requisições sem credencial ou com token forjado recebem 401; operações sem permissão recebem 403; apenas um fluxo administrativo autenticado altera papéis.

### [CRITICAL] AUD-002 — Segredos hardcoded e hash de senha exposto nas respostas

- **Arquivo e linhas:** `app.py:11-15`; `services/notification_service.py:5-20`; `models/user.py:16-25`; `routes/user_routes.py:27-40`, `routes/user_routes.py:80-86`, `routes/user_routes.py:127-129`, `routes/user_routes.py:207-211`
- **Categoria:** AP-02 — Segredos e dados sensíveis expostos
- **Evidência:** chave de aplicação e credencial SMTP-like estão em literais no código (valores omitidos). `User.to_dict()` inclui a coluna `password`, que contém o hash, e esse método alimenta respostas de consulta, criação, atualização e login.
- **Descrição:** configuração secreta e representação pública da entidade não estão separadas. A autenticidade operacional da credencial SMTP-like não pode ser determinada estaticamente; mesmo como default, ela é insegura.
- **Impacto:** vazamento do repositório pode comprometer sessões/serviço SMTP; hashes expostos permitem ataque offline contra senhas e ampliam o dano de acesso não autenticado.
- **Recomendação:** remover segredos do código, carregar por ambiente/secret manager, rotacionar valores se forem reais e criar DTO público que jamais serialize `password`.
- **Critério de aceite:** busca estática não encontra segredos versionados; respostas de todos os endpoints omitem senha/hash; aplicação falha de forma segura quando segredo obrigatório não está configurado.

### [HIGH] AUD-003 — Senhas armazenadas com MD5 sem salt

- **Arquivo e linhas:** `models/user.py:27-32`; `seed.py:16-35`
- **Categoria:** AP-07 — Criptografia insegura
- **Evidência:** `set_password` e `check_password` calculam diretamente `hashlib.md5(pwd.encode()).hexdigest()`; o seed cria contas com senhas fracas conhecidas.
- **Descrição:** MD5 rápido e sem salt não é um password hasher e permite comparação eficiente contra dicionários e tabelas pré-computadas.
- **Impacto:** uma leitura do banco ou a exposição descrita em AUD-002 facilita recuperação das senhas, inclusive reutilizadas em outros sistemas.
- **Recomendação:** migrar para Argon2, scrypt ou bcrypt por biblioteca mantida, com salt/custo adequados e estratégia de rehash; trocar credenciais de demonstração em ambientes não locais.
- **Critério de aceite:** novos hashes usam algoritmo adaptativo com salt; login migra ou rejeita hashes MD5 de forma planejada; testes comprovam verificação e não exposição.

### [HIGH] AUD-004 — Routes concentram HTTP, persistência e regras de negócio

- **Arquivo e linhas:** `routes/task_routes.py:11-299`; `routes/user_routes.py:10-211`; `routes/report_routes.py:12-223`
- **Categoria:** AP-04 — God Module; AP-05 — Regra de negócio em route/controller
- **Evidência:** handlers validam políticas de status/prioridade/papel, calculam atraso e produtividade, serializam entidades e controlam `db.session`; `summary_report` realiza consultas e agregações entre as linhas 15-99, e criação/alteração de task ocupa as linhas 85-223.
- **Descrição:** a separação por arquivos é nominal; não há controllers/use cases/repositories que isolem os casos de uso. O model já possui validações em `models/task.py:38-60`, mas as routes as duplicam.
- **Impacto:** mudanças de regra exigem editar múltiplos endpoints, testes unitários ficam difíceis e transações, erros e políticas tendem a divergir.
- **Recomendação:** manter Blueprints como adapters HTTP, extrair casos de uso/services por domínio e repositories, e centralizar invariantes/DTOs sem alterar contratos HTTP.
- **Critério de aceite:** routes apenas traduzem request/response; regras são exercitáveis sem contexto Flask; acesso ao ORM fica atrás de unidade transacional/repository.

### [MEDIUM] AUD-005 — Debug, CORS e inicialização do schema configurados no entry point

- **Arquivo e linhas:** `app.py:9-16`, `app.py:30-34`
- **Categoria:** AP-13 — Configuração hardcoded
- **Evidência:** URI SQLite, chave, CORS sem restrição explícita, host/porta e `debug=True` estão fixos; `db.create_all()` é executado durante importação da aplicação.
- **Descrição:** configuração de desenvolvimento, segurança de origem e lifecycle do schema não variam por ambiente nem possuem composition root/factory.
- **Impacto:** execução direta expõe debugger em todas as interfaces, CORS é mais permissivo que o necessário e imports têm efeito colateral sobre o banco.
- **Recomendação:** introduzir configuração por ambiente, app factory/composition root, allowlist CORS explícita e gestão de schema separada do import/boot.
- **Critério de aceite:** produção inicia com debug desabilitado, origens permitidas são configuráveis e importar a aplicação não cria/altera schema.

### [MEDIUM] AUD-006 — Consultas N+1 na listagem e nos relatórios

- **Arquivo e linhas:** `routes/task_routes.py:14-59`; `routes/report_routes.py:53-68`, `routes/report_routes.py:157-165`; `routes/user_routes.py:10-24`
- **Categoria:** AP-09 — Query N+1
- **Evidência:** para cada task são feitas buscas adicionais de usuário e categoria; para cada usuário e categoria há nova consulta/contagem. `len(u.tasks)` também pode disparar lazy load por usuário.
- **Descrição:** relações e agregações são resolvidas dentro de loops em vez de eager loading, join ou consultas agrupadas.
- **Impacto:** o número de queries cresce linearmente com os registros e pode degradar latência e capacidade rapidamente.
- **Recomendação:** usar eager loading para relações e agregações SQL agrupadas/buscas em lote; medir queries nos testes.
- **Critério de aceite:** a quantidade de queries dos endpoints afetados permanece constante ou limitada ao crescer o número de entidades.

### [MEDIUM] AUD-007 — Validação de entrada ausente ou inconsistente

- **Arquivo e linhas:** `routes/task_routes.py:85-144`, `routes/task_routes.py:156-213`, `routes/task_routes.py:240-265`; `routes/user_routes.py:42-78`, `routes/user_routes.py:92-125`; `routes/report_routes.py:167-180`, `routes/report_routes.py:190-202`; `utils/helpers.py:57-108`
- **Categoria:** AP-10 — Validação ausente ou inconsistente
- **Evidência:** create/update repetem regras com diferenças; comparações de `priority` assumem tipo numérico e filtros convertem query params com `int()` sem captura; update de categoria usa `data` sem checar JSON ausente e não valida nome/cor. Há um `process_task_data` centralizado, mas ele não é usado.
- **Descrição:** não existe schema/DTO único na borda e alguns tipos/formatos são aceitos sem validação consistente.
- **Impacto:** entradas malformadas geram 500, dados inválidos podem persistir e regras variam conforme o endpoint.
- **Recomendação:** aplicar schemas Marshmallow (dependência já declarada) ou DTOs equivalentes a create, update e query params, mantendo invariantes no domínio.
- **Critério de aceite:** matriz de entradas inválidas retorna 400 estável; create/update compartilham regras declaradas; constraints de domínio não dependem só da route.

### [MEDIUM] AUD-008 — Tratamento de erros genérico e observabilidade insuficiente

- **Arquivo e linhas:** `routes/task_routes.py:62-63`, `routes/task_routes.py:135-154`, `routes/task_routes.py:202-238`; `routes/user_routes.py:80-90`, `routes/user_routes.py:127-151`; `routes/report_routes.py:182-223`; `utils/helpers.py:43-50`, `utils/helpers.py:81-89`; `services/notification_service.py:12-25`
- **Categoria:** AP-11 — Tratamento de erros disperso ou silencioso
- **Evidência:** há múltiplos `except:` que capturam inclusive exceções de controle, respostas 500 sem registro da causa e logs via `print`; em outros pontos a exceção é capturada como `e` mas ignorada ou impressa sem estrutura.
- **Descrição:** cada handler define seu próprio tratamento e não há error handler central nem logging estruturado.
- **Impacto:** defeitos e falhas operacionais ficam ocultos, erros de programação são confundidos com falhas esperadas e diagnóstico/alerta ficam frágeis.
- **Recomendação:** capturar exceções específicas, centralizar mapeamento para HTTP, preservar rollback e usar logging estruturado com redaction.
- **Critério de aceite:** falhas esperadas possuem resposta determinística; falhas inesperadas geram correlação/log sem dados sensíveis; nenhum `except:` permanece no caminho web.

### [MEDIUM] AUD-009 — Interface ORM legada na versão declarada

- **Arquivo e linhas:** `routes/task_routes.py:42-52`, `routes/task_routes.py:67`, `routes/task_routes.py:117-123`, `routes/task_routes.py:158`, `routes/task_routes.py:188-196`, `routes/task_routes.py:227`; `routes/user_routes.py:29`, `routes/user_routes.py:94`, `routes/user_routes.py:136`, `routes/user_routes.py:155`; `routes/report_routes.py:105`, `routes/report_routes.py:192`, `routes/report_routes.py:213`
- **Categoria:** AP-12 — API deprecated ou legada
- **Evidência:** o projeto declara Flask-SQLAlchemy 3.1.1 e usa repetidamente `Model.query.get(...)`. A documentação 3.1.x classifica a interface `Model.query` como legada; SQLAlchemy 2.0 classifica `Query.get()` como legado/deprecated e indica `Session.get()`.
- **Descrição:** o acesso por PK depende da façade `Query` da API 1.x em uma stack 2.x/3.1.x.
- **Impacto:** warnings e dívida de migração aumentam; evolução para APIs modernas fica mais custosa.
- **Recomendação:** substituir lookups por `db.session.get(Model, id)`; migrar consultas gradualmente para `select()` + `session.execute/scalars`, verificando os contratos.
- **Critério de aceite:** busca estática e testes não apontam `Query.get()`; endpoints mantêm status e payloads.

### [MEDIUM] AUD-010 — Política de integridade referencial incompleta na exclusão de categorias

- **Arquivo e linhas:** `models/task.py:13-21`; `routes/report_routes.py:211-223`; `routes/user_routes.py:134-151`
- **Categoria:** AP-16 — Integridade referencial e exclusão inconsistente
- **Evidência:** as FKs de task são opcionais e relacionamentos não declaram política de cascade; exclusão de usuário remove tasks manualmente, enquanto exclusão de categoria remove somente a categoria.
- **Descrição:** entidades relacionadas recebem políticas de exclusão distintas, dependentes do comportamento do SQLite/ORM no runtime.
- **Impacto:** a exclusão de categoria pode falhar, nulificar referência implicitamente ou deixar referência órfã caso enforcement esteja desativado; o comportamento persistido não está explícito.
- **Recomendação:** decidir e implementar política explícita (restrict, set null ou cascade) no ORM e banco, com transação e testes de integração.
- **Critério de aceite:** testes provam a mesma política em usuário e categoria e não deixam tasks com referências inválidas.

### [MEDIUM] AUD-011 — Listagens e relatórios carregam conjuntos completos sem limite

- **Arquivo e linhas:** `routes/task_routes.py:11-61`, `routes/task_routes.py:240-271`, `routes/task_routes.py:273-299`; `routes/user_routes.py:10-25`, `routes/user_routes.py:153-183`; `routes/report_routes.py:12-101`, `routes/report_routes.py:157-165`
- **Categoria:** AP-15 — Legibilidade/performance de funções longas; risco operacional associado
- **Evidência:** endpoints usam `.all()` e serializam/processam todos os registros; relatórios fazem várias contagens e também carregam todas as tasks/usuários. Não há `page`, `per_page` ou limite máximo.
- **Descrição:** os contratos de coleção não impõem limites e parte das agregações ocorre em memória.
- **Impacto:** crescimento dos dados aumenta memória, tempo de resposta e risco de exaustão de recursos por chamadas públicas.
- **Recomendação:** adicionar paginação com limite máximo aos endpoints de coleção e mover agregações para SQL, preservando ou versionando cuidadosamente o contrato atual.
- **Critério de aceite:** testes com volume comprovam limite previsível e consumo estável; respostas documentam paginação.

### [LOW] AUD-012 — Regras e serializações duplicadas

- **Arquivo e linhas:** `models/task.py:23-60`; `routes/task_routes.py:14-59`, `routes/task_routes.py:65-81`, `routes/task_routes.py:85-144`, `routes/task_routes.py:156-215`, `routes/task_routes.py:273-297`; `routes/user_routes.py:153-181`; `routes/report_routes.py:30-43`, `routes/report_routes.py:119-151`; `utils/helpers.py:57-108`
- **Categoria:** AP-14 — Duplicação
- **Evidência:** serialização de task, cálculo de atraso, listas de status e validação de campos são repetidos em models, routes e helper não utilizado.
- **Descrição:** o mesmo conceito possui implementações paralelas que já retornam formatos diferentes (por exemplo, presença do campo `overdue`).
- **Impacto:** correções podem atingir um endpoint e não outro, produzindo divergências silenciosas.
- **Recomendação:** definir DTOs/serializadores e políticas de domínio únicos, reutilizados pelos casos de uso; preservar diferenças contratuais intencionais.
- **Critério de aceite:** cada regra compartilhada tem uma implementação e testes cobrem todos os adapters que a utilizam.

### [LOW] AUD-013 — Imports mortos e módulos sem integração efetiva

- **Arquivo e linhas:** `app.py:7`; `models/task.py:3`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `routes/report_routes.py:7-8`; `utils/helpers.py:3-7`; `services/notification_service.py:4-48`
- **Categoria:** AP-15 — Nomenclatura e legibilidade deficientes
- **Evidência:** vários imports não são referenciados; helpers importados em `report_routes.py` não são usados; `NotificationService` e vários helpers não são ligados ao fluxo HTTP observado.
- **Descrição:** código morto ou desconectado obscurece as dependências reais e sugere limites arquiteturais incompletos.
- **Impacto:** aumenta ruído, dificulta revisão e pode induzir manutenção de funcionalidades que não são alcançáveis.
- **Recomendação:** remover imports mortos e, após confirmar requisitos, integrar serviços por casos de uso ou remover código não utilizado.
- **Critério de aceite:** análise estática não reporta imports mortos e todo service/helper mantido tem consumidor e teste identificável.

## APIs deprecated ou legadas

- **Dependências verificadas:** Flask 3.0.0, Flask-SQLAlchemy 3.1.1, Flask-CORS 4.0.0, Marshmallow 3.20.1, Requests 2.31.0 e python-dotenv 1.0.0, todos com pins exatos em `requirements.txt:1-6`. O projeto não possui lockfile transitivo nem declara a versão do Python/SQLAlchemy resolvida.
- **Resultado:** confirmada em AUD-009 a interface legada `Model.query` e, especificamente, `Query.get()`. Não foram comprovadas outras depreciações no escopo estático.
- **Fonte da confirmação:** documentação oficial Flask-SQLAlchemy 3.1.x, seção “Legacy Query Interface” (`https://flask-sqlalchemy.palletsprojects.com/en/stable/legacy-query/`), e documentação oficial SQLAlchemy 2.0, “Legacy Query API” (`https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html`).

## Plano recomendado

1. Remover hashes das respostas, externalizar/rotacionar segredos, substituir MD5 e implementar autenticação/autorização real.
2. Criar app factory/composition root; separar routes, controllers/use cases, DTOs e repositories por domínio.
3. Tornar transações e políticas de exclusão explícitas; eliminar N+1 e introduzir paginação/agregação SQL.
4. Centralizar validação e erros; migrar a API ORM legada; remover duplicação e código morto.
5. Antes de editar, capturar baseline de boot e contratos dos 22 endpoints; após cada incremento, executar testes e smoke tests comparativos.

## Limitações

- As Fases 1 e 2 não executam instalação, boot, seed, testes ou migrations; nenhum resultado funcional foi alegado.
- Não há suíte/comando de testes, lint, lockfile transitivo, migration ou arquivo de exemplos HTTP no projeto analisado.
- A versão do Python e a versão transitiva de SQLAlchemy não estão declaradas; a análise de legado usa o contrato da dependência direta Flask-SQLAlchemy 3.1.1 e sua documentação oficial.
- O efeito exato da exclusão de categoria depende do enforcement de FK e comportamento ORM em runtime, a confirmar na baseline.
- A credencial SMTP-like foi mascarada; sua validade não foi testada nem presumida.

## Confirmação

Fase 2 concluída. Deseja prosseguir com a refatoração (Fase 3)? [s/n]

## Validação pós-refatoração

Refatoração autorizada explicitamente pelo usuário após a Fase 2. A estrutura foi migrada para app factory/composition root, routes, controllers, services e repositories. Os paths, métodos, payloads e status de sucesso originais foram preservados, exceto pela correção de segurança documentada: endpoints antes públicos agora exigem autenticação e, quando aplicável, papel/recurso autorizado; hashes de senha deixaram de compor respostas.

| Finding | Estado | Evidência |
|---|---|---|
| AUD-001 | Corrigido | `auth.py:1`; `routes/task_routes.py:1`; `routes/user_routes.py:1`; `routes/report_routes.py:1`; testes `test_authentication_and_role_enforcement` e `test_public_registration_cannot_choose_admin_role` |
| AUD-002 | Corrigido | `config.py:1`; `models/user.py:21`; `services/notification_service.py:5`; teste `_login` confirma ausência de `password` |
| AUD-003 | Mitigado | `models/user.py:27`: Werkzeug gera/verifica hash adaptativo; MD5 permanece somente para reconhecer hashes legados e é substituído após login válido |
| AUD-004 | Corrigido | `controllers/`, `services/`, `repositories/` e builders em `routes/`; busca estática não encontra ORM/database nas routes |
| AUD-005 | Corrigido | `config.py:1`; `app.py:18` (`create_app`); `app.py:63` usa debug/host/porta configuráveis; criação de schema saiu do import/boot |
| AUD-006 | Corrigido | `repositories/task_repository.py:9` usa eager loading; `repositories/user_repository.py:9` usa select-in; `repositories/category_repository.py:9` agrega contagens |
| AUD-007 | Corrigido | `services/validators.py:1`; validação compartilhada nos services de task/user/report; testes de entrada inválida passam |
| AUD-008 | Corrigido | `errors.py:1` centraliza tradução/log; services fazem rollback; busca estática não encontra `except:` genérico |
| AUD-009 | Corrigido | repositories usam `db.session.get`, `select` e `session.scalars`; busca estática não encontra `Model.query`/`Query.get` |
| AUD-010 | Corrigido | `repositories/category_repository.py:25` aplica explicitamente `SET NULL` antes da exclusão; teste de integração confirma task preservada sem referência |
| AUD-011 | Mitigado | N+1 e agregações principais foram corrigidos, mas coleções ainda não possuem paginação para evitar mudança silenciosa no formato de resposta |
| AUD-012 | Mitigado | serialização base e cálculo de atraso estão centralizados nos models/services; helpers antigos permanecem por compatibilidade |
| AUD-013 | Mitigado | imports mortos do caminho principal foram removidos; `NotificationService` e helpers continuam disponíveis, embora sem integração HTTP comprovada |

### Comandos executados

```text
python --version
→ Python 2.7.18; baseline documentada falhou ao interpretar f-strings e não possuía Flask.

python3 --version
→ Python 3.11.11.

python3 -m unittest discover -s tests -v
→ baseline ambiental: BLOCKED, ModuleNotFoundError: flask.

python3 -m venv /tmp/task-manager-audit-venv
/tmp/task-manager-audit-venv/bin/pip install -r requirements.txt
→ PASS; dependências instaladas somente em ambiente descartável autorizado.

/tmp/task-manager-audit-venv/bin/python -m unittest discover -s tests -v
→ PASS; 5 testes, 0 falhas.

DATABASE_URL=sqlite:////tmp/task-manager-audit-smoke.db .../python seed.py
→ PASS; banco descartável criado com 3 usuários, 4 categorias e 10 tasks.

python3 -c "ast.parse(...)"
→ PASS; todos os arquivos Python analisados sintaticamente.

git diff --check
→ PASS; nenhum erro de whitespace.

rg para Model.query, Query.get, token fictício, segredos antigos, debug=True e except:
→ PASS; nenhuma ocorrência ativa, exceto MD5 deliberadamente restrito à migração de hashes legados.
```

### Boot e endpoints

| Verificação | Resultado | Evidência |
|---|---|---|
| Boot | PASS | `SECRET_KEY=*** HOST=127.0.0.1 PORT=5057 FLASK_DEBUG=false .../python app.py`; servidor iniciou sem traceback |
| `GET /health` | PASS | HTTP 200, JSON com `status: ok` e timestamp |
| `GET /` | PASS | HTTP 200, shape original `{message, version}` |
| `GET /tasks` sem token | PASS | HTTP 401, autenticação obrigatória |
| `GET /tasks` com token admin | PASS | HTTP 200, `application/json`, servidor real com SQLite descartável |
| Inventário HTTP | PASS | teste compara exatamente os 22 pares método/path explícitos originais |
| `POST /login` | PASS | teste retorna 200, token assinado e usuário sem hash |
| Registro público com `role=admin` | PASS | HTTP 201, papel persistido/retornado como `user` |
| CRUD de task | PASS | criação 201, entrada inválida 400, atualização 200 e exclusão 200 em SQLite in-memory |
| Exclusão de categoria | PASS | HTTP 200 e task associada preservada com `category_id = null` |
| Relatório com usuário comum/admin | PASS | usuário recebe 403; admin recebe 200 |
| `GET /reports/summary` autenticado | PASS | HTTP 200, `application/json`, servidor real |
| `POST /tasks` inválido autenticado | PASS | HTTP 400, `application/json`, servidor real |

### Nova estrutura

```text
app.py                         # app factory e composition root
config.py                      # configuração por ambiente
auth.py / errors.py            # autenticação/autorização e erros centrais
models/                        # entidades ORM e invariantes locais
repositories/                  # acesso SQLAlchemy 2.x e política de persistência
services/                      # casos de uso, validação e relatórios
controllers/                   # orquestração e contrato de aplicação
routes/                        # adapters HTTP/Blueprints
tests/                         # caracterização, segurança e integração
```

### Achados residuais e limitações

- AUD-011 permanece mitigado: paginação mudaria o formato de coleções e requer decisão explícita de versionamento/compatibilidade.
- AUD-012 e AUD-013 permanecem mitigados por helpers e serviço de notificação sem consumidores observados; foram preservados para evitar remoção incompatível sem evidência de uso externo.
- O reconhecimento temporário de MD5 em `User.check_password` é necessário para migração transparente dos dados existentes; um login válido regrava imediatamente o hash com Werkzeug. A remoção definitiva depende de confirmar que não restam hashes legados.
- O comando antigo `python app.py` continua inviável neste host porque `python` aponta para 2.7; o README foi corrigido para `python3`.
- O venv de validação está em `/tmp/task-manager-audit-venv` e não altera dependências do projeto ou do sistema.
- O banco SQLite usado nos smoke tests foi removido de `/tmp` após a validação; continha apenas fixtures descartáveis e não é recuperável.
