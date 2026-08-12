# Skill de Auditoria e Refatoração Arquitetural com Codex

Este repositório contém o desenvolvimento de uma Custom Skill para o OpenAI Codex capaz de analisar projetos, identificar problemas de arquitetura, segurança e qualidade, produzir um relatório de auditoria e, mediante confirmação, refatorar a aplicação para uma arquitetura baseada em MVC.

Os projetos usados como casos de teste são:

- `code-smells-project/`: API de e-commerce em Python e Flask;
- `ecommerce-api-legacy/`: API de LMS e checkout em Node.js e Express;
- `task-manager-api/`: API de gerenciamento de tarefas em Python e Flask, parcialmente organizada em camadas.

## Ferramenta escolhida

A ferramenta escolhida para o desafio é o **OpenAI Codex**. Portanto, os exemplos do enunciado baseados no Claude Code foram adaptados para a convenção do Codex, mantendo o nome obrigatório `refactor-arch`, um arquivo principal `SKILL.md` e arquivos de referência em Markdown.

A estrutura implementada é:

```text
.agents/
└── skills/
    └── refactor-arch/
        ├── SKILL.md
        └── references/
            ├── project-analysis.md
            ├── anti-pattern-catalog.md
            ├── audit-report-template.md
            ├── mvc-guidelines.md
            ├── refactoring-playbook.md
            └── validation-guide.md
```

## Escala de severidade

- **CRITICAL:** falha grave de segurança ou arquitetura, com risco de exposição de dados, comprometimento do sistema ou violação completa da separação de responsabilidades.
- **HIGH:** violação forte de MVC ou SOLID que prejudica significativamente manutenção, evolução e testes.
- **MEDIUM:** problema de padronização, duplicação, validação, tratamento de erros ou desempenho moderado.
- **LOW:** problema localizado de legibilidade, nomenclatura, constantes mágicas ou higiene de código.

## Análise Manual

Esta seção constitui a linha de base manual que será usada posteriormente para avaliar a capacidade de detecção da skill. A análise foi exclusivamente estática: nesta etapa as aplicações não foram executadas, dependências não foram instaladas e nenhum código-fonte foi refatorado.

### Resumo dos achados

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---:|---:|---:|---:|---:|
| `code-smells-project` | 3 | 1 | 2 | 2 | 8 |
| `ecommerce-api-legacy` | 2 | 2 | 2 | 2 | 8 |
| `task-manager-api` | 3 | 1 | 2 | 2 | 8 |
| **Total** | **8** | **4** | **6** | **6** | **24** |

### Projeto 1 — `code-smells-project`

**Stack e arquitetura observadas:** Python, Flask e SQLite. A aplicação separa superficialmente entry point, controllers, acesso a dados e inicialização do banco, mas concentra múltiplos domínios em arquivos extensos e permite que rotas acessem diretamente o banco.

#### CSP-01 — Execução remota de SQL sem autenticação

- **Severidade:** CRITICAL
- **Localização:** `code-smells-project/app.py:59-78`
- **Evidência:** a rota `POST /admin/query` recebe o campo `sql` da requisição e o entrega diretamente a `cursor.execute(query)`.
- **Impacto:** qualquer cliente com acesso à API pode ler, alterar ou apagar dados e modificar o schema. A verificação textual de `SELECT` apenas muda o formato da resposta e não restringe a operação executada.
- **Recomendação:** remover a rota da aplicação. Operações administrativas devem usar serviços restritos, comandos predefinidos, autorização e trilha de auditoria.

#### CSP-02 — SQL Injection nas operações de dados

- **Severidade:** CRITICAL
- **Localização:** `code-smells-project/models.py:43-60`, `models.py:105-110`, `models.py:122-129` e `models.py:285-299`
- **Evidência:** valores recebidos da API, como nome, descrição, e-mail, senha, termo e categoria, são concatenados diretamente em instruções SQL.
- **Impacto:** entradas maliciosas podem alterar a semântica das queries, expor dados, contornar o login ou corromper o banco.
- **Recomendação:** usar placeholders e parâmetros do driver SQLite em todas as queries; manter construção dinâmica limitada a trechos controlados pela aplicação.

#### CSP-03 — Credenciais em texto puro e expostas pela API

- **Severidade:** CRITICAL
- **Localização:** `code-smells-project/database.py:27-34`, `database.py:75-82` e `models.py:72-103`
- **Evidência:** a coluna `senha` armazena texto puro, os seeds incluem senhas legíveis e as funções de consulta devolvem esse campo ao controller.
- **Impacto:** uma leitura do banco ou uma chamada aos endpoints de usuários compromete imediatamente todas as credenciais armazenadas.
- **Recomendação:** armazenar hashes com algoritmo apropriado para senhas, nunca serializar o hash e usar um DTO de resposta sem campos sensíveis.

#### CSP-04 — Módulos com responsabilidades excessivas

- **Severidade:** HIGH
- **Localização:** `code-smells-project/controllers.py:5-292` e `models.py:4-314`
- **Evidência:** os mesmos módulos concentram produtos, usuários, autenticação, pedidos, estoque, notificações, relatórios, health check, SQL e serialização.
- **Impacto:** alto acoplamento entre domínios, baixa coesão e dificuldade para testar ou evoluir uma funcionalidade isoladamente.
- **Recomendação:** separar routes/views, controllers e models/repositories por domínio; mover regras transacionais e casos de uso para serviços específicos.

#### CSP-05 — Queries N+1 ao carregar pedidos

- **Severidade:** MEDIUM
- **Localização:** `code-smells-project/models.py:171-200` e `models.py:203-233`
- **Evidência:** para cada pedido é feita uma consulta de itens e, para cada item, outra consulta do produto.
- **Impacto:** o número de queries cresce com a quantidade de pedidos e itens, degradando progressivamente a latência do endpoint.
- **Recomendação:** carregar os dados com `JOIN`, consultas em lote ou um repositório que componha o agregado de forma eficiente.

#### CSP-06 — Conexão global mutável com concorrência desabilitada

- **Severidade:** MEDIUM
- **Localização:** `code-smells-project/database.py:4-11`
- **Evidência:** uma única conexão global é compartilhada e criada com `check_same_thread=False`.
- **Impacto:** requisições concorrentes podem compartilhar estado e transações, dificultando isolamento, testes e recuperação consistente de erros.
- **Recomendação:** gerenciar conexões por contexto de requisição, com fechamento automático e limites transacionais claros.

#### CSP-07 — Regras e validações duplicadas nos controllers

- **Severidade:** LOW
- **Localização:** `code-smells-project/controllers.py:24-62` e `controllers.py:64-96`
- **Evidência:** criação e atualização de produto repetem extração de campos e validações de preço, estoque e nome.
- **Impacto:** alterações de regra podem ser aplicadas em um fluxo e esquecidas no outro, produzindo comportamento inconsistente.
- **Recomendação:** centralizar validação em schema ou componente reutilizável, mantendo o controller focado na orquestração HTTP.

#### CSP-08 — Constantes de ambiente e negócio espalhadas no código

- **Severidade:** LOW
- **Localização:** `code-smells-project/app.py:7-9`, `app.py:88`, `controllers.py:52` e `models.py:256-262`
- **Evidência:** chave secreta, debug, host, porta, categorias e faixas de desconto aparecem como literais em diferentes módulos.
- **Impacto:** configuração por ambiente e alterações nas regras exigem edição direta do código.
- **Recomendação:** extrair configuração para variáveis de ambiente e regras de negócio para constantes ou políticas nomeadas.

### Projeto 2 — `ecommerce-api-legacy`

**Stack e arquitetura observadas:** Node.js, Express e SQLite em memória. O entry point delega toda a inicialização, persistência, roteamento e lógica de checkout para uma única classe.

#### EAL-01 — Segredos de produção hardcoded

- **Severidade:** CRITICAL
- **Localização:** `ecommerce-api-legacy/src/utils.js:1-6`
- **Evidência:** credencial de banco, chave de gateway identificada como `pk_live` e usuário SMTP estão versionados no código.
- **Impacto:** qualquer pessoa com acesso ao repositório pode obter credenciais e chaves operacionais; o histórico Git preserva o vazamento mesmo após remoção simples.
- **Recomendação:** revogar e rotacionar os segredos, carregá-los de variáveis de ambiente ou secret manager e impedir novos vazamentos com scanning automatizado.

#### EAL-02 — Dados completos de cartão registrados em log

- **Severidade:** CRITICAL
- **Localização:** `ecommerce-api-legacy/src/AppManager.js:28-46`
- **Evidência:** `req.body.card` é interpolado integralmente em `console.log` junto da chave do gateway.
- **Impacto:** dados de pagamento e credenciais podem ser expostos em logs, backups, observabilidade e consoles, ampliando o impacto de acesso indevido.
- **Recomendação:** nunca receber ou registrar cartão bruto fora de um fluxo compatível com o provedor; usar tokenização e mascaramento de campos sensíveis.

#### EAL-03 — God Class mistura infraestrutura, HTTP e regras de negócio

- **Severidade:** HIGH
- **Localização:** `ecommerce-api-legacy/src/AppManager.js:4-138`
- **Evidência:** `AppManager` cria e popula tabelas, registra rotas, valida entrada, cadastra usuário, simula pagamento, cria matrícula, grava auditoria, gera relatório e remove usuário.
- **Impacto:** viola SRP e separação MVC, acopla regras ao Express e ao SQLite e torna testes isolados muito difíceis.
- **Recomendação:** separar composition root, routes, controllers, services/use cases e repositories por domínio.

#### EAL-04 — Algoritmo caseiro e inseguro para senhas

- **Severidade:** HIGH
- **Localização:** `ecommerce-api-legacy/src/utils.js:17-23` e `AppManager.js:66-72`
- **Evidência:** `badCrypto` repete uma transformação Base64 previsível e reduz o resultado a dez caracteres; quando a senha não é informada, usa `123456`.
- **Impacto:** hashes podem ser revertidos ou reproduzidos com baixo custo e contas diferentes podem compartilhar credenciais previsíveis.
- **Recomendação:** exigir senha válida e usar biblioteca consolidada com Argon2, scrypt ou bcrypt, salt único e parâmetros adequados.

#### EAL-05 — Checkout sem transação atômica

- **Severidade:** MEDIUM
- **Localização:** `ecommerce-api-legacy/src/AppManager.js:43-63`
- **Evidência:** matrícula, pagamento e auditoria são inseridos em callbacks independentes, sem `BEGIN`, `COMMIT` ou `ROLLBACK` conjunto.
- **Impacto:** uma falha intermediária pode deixar matrícula sem pagamento, pagamento sem auditoria ou outra combinação inconsistente.
- **Recomendação:** encapsular o caso de uso em uma transação e confirmar somente quando todas as escritas obrigatórias terminarem.

#### EAL-06 — Queries N+1 no relatório financeiro

- **Severidade:** MEDIUM
- **Localização:** `ecommerce-api-legacy/src/AppManager.js:80-129`
- **Evidência:** para cada curso são buscadas matrículas e, para cada matrícula, usuário e pagamento em consultas separadas.
- **Impacto:** quantidade de queries e callbacks cresce com cursos e matrículas, elevando latência e complexidade de controle assíncrono.
- **Recomendação:** gerar o relatório com joins e agregações ou consultas em lote, mantendo a montagem final fora do controller.

#### EAL-07 — Nomenclatura opaca no contrato de checkout

- **Severidade:** LOW
- **Localização:** `ecommerce-api-legacy/src/AppManager.js:29-33`
- **Evidência:** campos `usr`, `eml`, `pwd`, `c_id` e variáveis `u`, `e`, `p`, `cid`, `cc` escondem a intenção dos dados.
- **Impacto:** reduz a legibilidade, dificulta documentação e aumenta a chance de mapeamentos incorretos.
- **Recomendação:** adotar nomes completos no DTO e no código, como `userName`, `email`, `password`, `courseId` e `paymentToken`.

#### EAL-08 — Erros de callbacks ignorados

- **Severidade:** LOW
- **Localização:** `ecommerce-api-legacy/src/AppManager.js:57-61`, `AppManager.js:92-126` e `AppManager.js:131-136`
- **Evidência:** diversos callbacks recebem `err`, mas continuam a execução ou devolvem sucesso sem verificar a falha, inclusive na exclusão de usuário.
- **Impacto:** a API pode reportar sucesso quando a operação falhou e exceções podem surgir ao acessar resultados indefinidos.
- **Recomendação:** tratar todos os erros de persistência de forma centralizada e adotar promises/`async`-`await` para tornar o fluxo explícito.

### Projeto 3 — `task-manager-api`

**Stack e arquitetura observadas:** Python, Flask, Flask-SQLAlchemy e SQLite. Existem models, blueprints, services e utils, mas os arquivos de rota ainda acumulam serialização, validação, regras de negócio, consultas e transações.

#### TMA-01 — Senhas protegidas com MD5

- **Severidade:** CRITICAL
- **Localização:** `task-manager-api/models/user.py:27-32`
- **Evidência:** `set_password` e `check_password` usam MD5 direto, sem salt e sem fator de custo.
- **Impacto:** MD5 é inadequado para armazenamento de senhas e permite ataques offline muito rápidos em caso de vazamento do banco.
- **Recomendação:** migrar para Argon2, scrypt ou bcrypt por meio de uma biblioteca consolidada e planejar rehash das credenciais existentes.

#### TMA-02 — Hash de senha exposto pela serialização do usuário

- **Severidade:** CRITICAL
- **Localização:** `task-manager-api/models/user.py:16-25`, `routes/user_routes.py:10-25` e `routes/user_routes.py:207-210`
- **Evidência:** `User.to_dict()` inclui `password`; esse serializador é usado em respostas de criação e login. A listagem também oferece uma representação alternativa, evidenciando contratos inconsistentes.
- **Impacto:** hashes podem ser enviados a clientes e usados em ataques offline, agravados pelo uso de MD5.
- **Recomendação:** remover permanentemente credenciais de qualquer DTO de saída e criar serializadores explícitos para perfis público e administrativo.

#### TMA-03 — Autenticação fictícia e endpoints sem autorização

- **Severidade:** CRITICAL
- **Localização:** `task-manager-api/routes/user_routes.py:185-211`, `routes/user_routes.py:119-125` e `app.py:18-20`
- **Evidência:** o login retorna `fake-jwt-token-<id>`, previsível e sem assinatura; não existe middleware que valide token ou proteja alteração de `role`, usuários, relatórios e demais recursos.
- **Impacto:** autenticação e autorização não são efetivas, permitindo acesso e escalada de privilégio por clientes não confiáveis.
- **Recomendação:** implementar tokens assinados ou sessões seguras, middleware de autenticação e autorização por papel; impedir que o próprio cliente atribua papéis privilegiados.

#### TMA-04 — Controllers ausentes e regras concentradas nas rotas

- **Severidade:** HIGH
- **Localização:** `task-manager-api/routes/task_routes.py:11-299`, `routes/user_routes.py:10-211` e `routes/report_routes.py:12-223`
- **Evidência:** os blueprints fazem validação, consultas, serialização, cálculos, controle transacional e regras de status, prioridade, atraso e produtividade.
- **Impacto:** a organização por pastas não produz separação real de responsabilidades; regras ficam acopladas ao Flask e difíceis de testar sem contexto HTTP.
- **Recomendação:** manter routes/views responsáveis pelo protocolo HTTP, criar controllers/use cases para orquestração e repositories para persistência.

#### TMA-05 — Queries N+1 na listagem de tarefas e relatórios

- **Severidade:** MEDIUM
- **Localização:** `task-manager-api/routes/task_routes.py:14-59`, `routes/report_routes.py:53-68` e `routes/report_routes.py:157-165`
- **Evidência:** cada tarefa pode disparar consultas adicionais de usuário e categoria; relatórios consultam tasks por usuário e contam tasks por categoria dentro de loops.
- **Impacto:** o custo cresce proporcionalmente ao volume de entidades, gerando gargalo desnecessário.
- **Recomendação:** usar eager loading, joins e agregações no banco, mantendo os relatórios em um serviço de consulta dedicado.

#### TMA-06 — Uso de API legada do SQLAlchemy

- **Severidade:** MEDIUM
- **Localização:** `task-manager-api/routes/task_routes.py:67`, `task_routes.py:117-122`, `task_routes.py:158`, `routes/user_routes.py:29`, `user_routes.py:94` e `routes/report_routes.py:105`
- **Evidência:** o projeto usa repetidamente `Model.query.get(...)`, interface considerada legada no SQLAlchemy 2.x.
- **Impacto:** aumenta dívida de atualização e risco de incompatibilidade futura, além de espalhar detalhes do ORM pelas rotas.
- **Recomendação:** encapsular acesso em repositories e migrar buscas por chave para `db.session.get(Model, id)`.

#### TMA-07 — Exceções genéricas e imports sem uso

- **Severidade:** LOW
- **Localização:** `task-manager-api/routes/task_routes.py:7`, `task_routes.py:62`, `routes/user_routes.py:6`, `user_routes.py:130`, `utils/helpers.py:3-7` e `utils/helpers.py:43-50`
- **Evidência:** há imports agrupados e não utilizados e diversos `except:` que capturam inclusive exceções que não deveriam ser silenciadas.
- **Impacto:** reduz clareza, esconde causas de falha e dificulta diagnóstico e manutenção.
- **Recomendação:** remover imports não usados, capturar exceções específicas e centralizar logging e respostas de erro.

#### TMA-08 — Regras e serialização duplicadas

- **Severidade:** LOW
- **Localização:** `task-manager-api/models/task.py:23-60`, `routes/task_routes.py:14-59`, `routes/task_routes.py:92-114`, `routes/task_routes.py:166-215`, `routes/user_routes.py:153-183` e `utils/helpers.py:57-115`
- **Evidência:** serialização de task, cálculo de atraso, status válidos, prioridade e validação aparecem em models, rotas e helpers; algumas funções utilitárias nem são consumidas pelas rotas.
- **Impacto:** a mesma regra pode evoluir de formas diferentes, causando respostas e validações inconsistentes.
- **Recomendação:** definir uma única fonte para cada regra, adotar schemas/DTOs e reutilizar casos de uso entre criação, atualização e consulta.

## Critérios da análise manual

Os três projetos atendem aos mínimos exigidos para esta etapa:

- [x] pelo menos cinco problemas documentados por projeto;
- [x] pelo menos um problema CRITICAL ou HIGH por projeto;
- [x] pelo menos dois problemas MEDIUM por projeto;
- [x] pelo menos dois problemas LOW por projeto;
- [x] severidade justificada por impacto;
- [x] arquivo e linhas informados para cada evidência;
- [x] recomendação registrada para cada achado;
- [x] diferentes níveis de organização e as duas stacks contemplados.

## Construção da Skill

A skill `refactor-arch` foi criada em `.agents/skills/refactor-arch/`, seguindo a convenção de skills de projeto do Codex. Essa pasta funcionou como fonte única durante o desenvolvimento e, após validação, foi copiada para os três projetos-alvo. As quatro cópias foram validadas e possuem conteúdo idêntico.

O `SKILL.md` implementa três fases sequenciais:

1. **Análise:** detecta stack, persistência, domínio, arquitetura, arquivos, linhas, entry point e comandos disponíveis sem modificar o projeto.
2. **Auditoria:** cruza o código contra o catálogo, gera relatório com evidências e encerra o turno solicitando confirmação explícita.
3. **Refatoração:** somente após confirmação, aplica MVC incrementalmente e valida análise estática, testes, boot e endpoints.

As principais decisões de design foram:

- separar o procedimento essencial no `SKILL.md` do conhecimento detalhado em referências carregadas por fase;
- usar evidências combinadas de manifestos, lockfiles, imports e código, em vez de depender de extensões ou nomes de pastas;
- definir responsabilidades arquiteturais independentes de linguagem, com adaptações idiomáticas para Flask e Express;
- impedir qualquer edição antes da confirmação humana posterior ao relatório;
- preservar contratos HTTP e mudanças preexistentes durante a refatoração;
- exigir reauditoria e evidência real antes de declarar um finding corrigido.

O catálogo contém 16 anti-patterns distribuídos entre CRITICAL, HIGH, MEDIUM e LOW, incluindo injeção, segredos, autenticação, God Class, acoplamento, criptografia insegura, transações, N+1, validação, erros, APIs deprecated, configuração, duplicação e integridade referencial. A detecção de depreciações exige confirmação contra a versão declarada e uma fonte oficial, evitando classificar como deprecated apenas por existir uma alternativa moderna.

O playbook contém 12 transformações com exemplos antes/depois para Python e JavaScript. Entre elas estão parametrização de SQL, extração de configuração, hashing de senha, separação de routes/controllers/services, decomposição de God Modules, transações, eager loading, error handler, schemas, migração de APIs legadas, autenticação verificável e composition root.

A estrutura foi verificada com o validador oficial da `skill-creator`; frontmatter, nome e arquivos obrigatórios foram considerados válidos. Em seguida, a mesma skill foi executada em dois projetos Python/Flask com diferentes níveis de organização e em um projeto Node.js/Express.

## Resultados

### Auditorias automatizadas

A skill encontrou mais que os cinco findings mínimos em todos os projetos e reproduziu os principais problemas levantados manualmente.

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---:|---:|---:|---:|---:|---|
| `code-smells-project` | 4 | 2 | 4 | 2 | 12 | `reports/audit-project-1.md` |
| `ecommerce-api-legacy` | 2 | 5 | 5 | 2 | 14 | `reports/audit-project-2.md` |
| `task-manager-api` | 2 | 2 | 7 | 2 | 13 | `reports/audit-project-3.md` |
| **Total** | **8** | **9** | **16** | **6** | **39** | |

Todos os relatórios:

- seguem o template da skill;
- apresentam arquivo e linhas para cada finding;
- ordenam findings por severidade;
- registram a análise de APIs deprecated/legadas;
- preservam a auditoria original e acrescentam a validação pós-refatoração;
- registram comandos, boot, testes, endpoints e limitações.

### Comparação antes e depois

| Projeto | Antes | Depois | Estado dos findings |
|---|---|---|---|
| `code-smells-project` | Quatro arquivos monolíticos, SQL remoto, SQL Injection, senhas em texto puro, conexão global e N+1 | App factory, config, models, repositories, services, controllers, routes, erros centrais, SQL parametrizado e hashing | 11 corrigidos e 1 mitigado |
| `ecommerce-api-legacy` | `AppManager` concentrava Express, SQLite, checkout, pagamentos e relatórios; segredos/logs inseguros, criptografia caseira, N+1 e ausência de transação | Composition root, routes, controllers, services, repositories, configuração externa, scrypt, autenticação administrativa, JOIN e transação com rollback | 13 corrigidos e 1 bloqueado |
| `task-manager-api` | Pastas existentes, mas routes acessavam ORM e concentravam regras; token previsível, MD5, hash exposto, N+1 e APIs ORM legadas | App factory, autenticação assinada, autorização, controllers, services, repositories SQLAlchemy 2.x, validação e erros centrais | 9 corrigidos e 4 mitigados |

Os estados mitigados ou bloqueados não foram ocultados:

- Projeto 1: bancos SQLite preexistentes precisam de migration para receber as novas foreign keys; novas bases já possuem constraints.
- Projeto 2: atualizar `sqlite3` para a major atual requer Node.js `>=20.17.0`, enquanto a execução disponível usou Node.js 14.21.3.
- Projeto 3: paginação alteraria o contrato das coleções; helpers sem consumidores comprovados foram preservados; o reconhecimento temporário de MD5 permite migrar hashes no próximo login válido.

### Estruturas resultantes

Os três projetos agora aplicam o mesmo conjunto de limites arquiteturais, respeitando as convenções de cada stack:

```text
HTTP routes/views
      ↓
controllers
      ↓
services/use cases
      ↓
models + repositories
      ↓
database / gateways
```

Configuração, autenticação/autorização e tratamento de erros foram extraídos para componentes próprios. Os entry points atuam como composition roots e conectam implementações concretas.

### Validação funcional

| Projeto | Testes finais | Boot real | Contrato HTTP |
|---|---|---|---|
| `code-smells-project` | 6/6 passando | PASS, Flask com debug desligado | 19 combinações método/path preservadas; endpoints críticos exercitados |
| `ecommerce-api-legacy` | 4/4 grupos passando | PASS, Express | Checkout, relatório, autenticação administrativa, exclusão, integridade e rollback validados |
| `task-manager-api` | 5/5 passando | PASS, Flask com debug desligado | 22 combinações método/path preservadas; autenticação, CRUD e relatórios validados |

Validação consolidada final:

```text
Projeto 1: 6 testes — OK
Projeto 2: 4 grupos — PASS
Projeto 3: 5 testes — OK
Skill raiz + 3 cópias — Skill is valid!
git diff --check — PASS
```

No teste de rollback do Projeto 2, uma falha SQLite é injetada deliberadamente no audit log. O erro é esperado e o teste comprova que usuários, matrículas e pagamentos retornam à baseline.

## Checklist de validação

### Fase 1 — Análise

- [x] Linguagem detectada corretamente nos três projetos.
- [x] Framework detectado corretamente nos três projetos.
- [x] Domínio descrito corretamente.
- [x] Persistência, entry point, arquivos e linhas inventariados.
- [x] Arquitetura atual mapeada por responsabilidades e dependências.

### Fase 2 — Auditoria

- [x] Relatórios seguem o template definido pela skill.
- [x] Cada finding possui arquivo e linhas exatos.
- [x] Findings estão ordenados de CRITICAL para LOW.
- [x] Todos os projetos possuem pelo menos cinco findings.
- [x] Todos os projetos possuem pelo menos um CRITICAL ou HIGH.
- [x] Detecção de APIs deprecated/legadas foi executada.
- [x] A skill interrompeu a execução e solicitou confirmação antes da Fase 3.
- [x] Três relatórios foram salvos em `reports/`.

### Fase 3 — Refatoração

- [x] Estrutura baseada em MVC nos três projetos.
- [x] Configuração extraída e segredos removidos do código.
- [x] Models e repositories encapsulam dados e persistência.
- [x] Views/routes estão separadas do fluxo de aplicação.
- [x] Controllers e services concentram orquestração e casos de uso.
- [x] Tratamento de erros centralizado.
- [x] Entry point/composition root claro.
- [x] Aplicações iniciam sem erros.
- [x] Endpoints originais foram inventariados e validados.
- [x] Testes automatizados passam nos três projetos.
- [x] Achados residuais estão explicitamente documentados.

## Como executar

### Pré-requisitos

- Git;
- Codex CLI autenticado;
- Python 3.11 ou compatível com os manifests Python;
- Node.js e npm para o projeto Express;
- acesso local para instalar dependências e abrir portas durante smoke tests.

Não versione arquivos `.env`. Use os `.env.example` de cada projeto e substitua os placeholders por valores locais seguros.

### Invocar a skill pelo Codex CLI

A skill já está presente em `.agents/skills/refactor-arch/` dentro de cada projeto. Entre no projeto desejado e inicie uma sessão nova, concedendo escrita adicional na raiz apenas para salvar o relatório compartilhado:

```bash
cd code-smells-project
codex --add-dir .. --ask-for-approval on-request
```

No Codex, invoque explicitamente:

```text
Use $refactor-arch neste projeto. Execute somente as Fases 1 e 2 inicialmente. Salve o relatório em ../reports/audit-project-1.md. Não modifique o código-fonte antes da minha confirmação explícita.
```

Use `audit-project-2.md` no `ecommerce-api-legacy` e `audit-project-3.md` no `task-manager-api`. Após revisar o relatório e a pergunta obrigatória da Fase 2, responda `sim` para autorizar a refatoração.

Também é possível iniciar com o prompt diretamente pelo shell:

```bash
codex --add-dir .. --ask-for-approval on-request \
  'Use $refactor-arch neste projeto. Execute somente as Fases 1 e 2 inicialmente. Salve o relatório em ../reports/audit-project-1.md. Não modifique o código-fonte antes da minha confirmação explícita.'
```

As aspas simples impedem que o shell tente expandir `$refactor-arch`. Use uma sessão nova para cada projeto, garantindo descoberta local da skill, contexto independente e nova barreira de confirmação.

### Projeto 1 — Python/Flask E-commerce

```bash
cd code-smells-project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m unittest discover -s tests -v
python app.py
```

O servidor usa `127.0.0.1:5000` por padrão. Configure as variáveis `APP_*` descritas em `.env.example`.

### Projeto 2 — Node.js/Express LMS

```bash
cd ecommerce-api-legacy
npm ci
npm test
ADMIN_API_KEY="uma-chave-aleatoria-com-16-ou-mais-caracteres" npm start
```

O servidor usa a porta 3000 por padrão. Os endpoints administrativos exigem a chave em `X-API-Key` ou `Authorization: Bearer <chave>`.

### Projeto 3 — Python/Flask Task Manager

```bash
cd task-manager-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
python -m unittest discover -s tests -v
python app.py
```

Após o seed, obtenha um token em `POST /login` e envie `Authorization: Bearer <token>` nos endpoints protegidos. Use `python3` quando o alias `python` apontar para uma versão antiga.

## Relatórios

- [`reports/audit-project-1.md`](reports/audit-project-1.md): e-commerce Python/Flask.
- [`reports/audit-project-2.md`](reports/audit-project-2.md): LMS Node.js/Express.
- [`reports/audit-project-3.md`](reports/audit-project-3.md): Task Manager Python/Flask.

Cada relatório contém a auditoria anterior às mudanças e a seção de validação pós-refatoração, permitindo rastrear a relação entre finding, transformação e evidência.
