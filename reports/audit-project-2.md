# Relatório de Auditoria Arquitetural — ecommerce-api-legacy

## Metadados

| Campo | Valor |
|---|---|
| Projeto | `ecommerce-api-legacy` |
| Stack | JavaScript (CommonJS) + Express 4.22.1 + SQLite (`sqlite3` 5.1.7) |
| Arquitetura observada | Monólito sem separação MVC; uma God Class concentra rotas, regras de negócio e persistência |
| Escopo | `src/*.js`, `package.json`, `package-lock.json`, `README.md` e `api.http`; excluídos `.git`, `node_modules`, dependências vendorizadas, builds, caches, cobertura e artefatos gerados |
| Arquivos analisados | 3 arquivos-fonte |
| Linhas aproximadas | 180 linhas físicas de JavaScript |
| Data | 2026-08-12 |
| Método | Análise estática orientada por evidências |

## Resumo executivo

A API é um monólito Express pequeno, mas concentra composição, acesso ao SQLite, definição de schema, rotas HTTP e regras dos domínios de usuários, cursos, matrículas, pagamentos e auditoria. Não existem controllers, services, models ou repositories separados; o fluxo predominante é `HTTP → AppManager → sqlite3`, e a própria rota executa o workflow de negócio.

Os riscos prioritários são de segurança: configuração contém credenciais e chave com formato operacional, o checkout registra cartão e chave em texto claro, uma senha seed é persistida em texto puro, e endpoints administrativos/destrutivos não têm autenticação nem autorização. Os valores sensíveis foram deliberadamente mascarados neste relatório; sua validade não pôde ser determinada por análise estática, portanto devem ser tratados como comprometidos e rotacionados caso tenham sido usados fora deste exemplo.

Também há risco concreto de inconsistência financeira: checkout grava usuário, matrícula, pagamento e log sem transação, e a exclusão de usuário deixa registros órfãos. O relatório financeiro executa consultas N+1 e ignora erros internos, podendo falhar silenciosamente ou nem concluir a resposta. Não foram executados boot, testes ou requisições nas Fases 1 e 2.

| Severidade | Quantidade |
|---|---:|
| CRITICAL | 2 |
| HIGH | 5 |
| MEDIUM | 5 |
| LOW | 2 |
| **Total** | **14** |

## Arquitetura atual

`src/app.js` cria o Express, ativa o parser JSON, instancia `AppManager`, inicializa o banco e delega à mesma classe o registro das três rotas. `AppManager` cria o SQLite em memória, define e popula cinco tabelas, interpreta requests, executa regras de checkout, acessa dados diretamente e formata responses. `src/utils.js` agrega configuração, credenciais, cache global, logging e uma rotina caseira de senha.

```text
HTTP → Express (`src/app.js`) → rotas/regras/SQL (`AppManager`) → sqlite3 em memória
                                      ↘ config/cache/crypto (`src/utils.js`)
```

Objetos de banco confirmados pelo DDL: `users`, `courses`, `enrollments`, `payments` e `audit_logs`. Não há camada explícita de middleware de autenticação, controller, service, model/entity ou repository.

## Findings

### [CRITICAL] AUD-001 — Segredos, cartão e senha expostos em texto claro

- **Arquivo e linhas:** `src/utils.js:1-6`; `src/AppManager.js:18-21`; `src/AppManager.js:45-46`
- **Categoria:** AP-02 — Segredos e dados sensíveis expostos
- **Evidência:** credenciais e uma chave com formato operacional estão literais no código (valores omitidos); o seed persiste senha sem hash; o checkout escreve no log o número completo do cartão e a chave de pagamento.
- **Descrição:** dados sensíveis não possuem externalização, hashing seguro nem redaction. A validade dos literais não é comprovável estaticamente.
- **Impacto:** exposição por repositório e logs, comprometimento de contas/integração e tratamento indevido de dados de pagamento. Se os valores tiverem uso real, devem ser considerados comprometidos.
- **Recomendação:** rotacionar valores potencialmente reais; carregar segredos por ambiente/secret manager; nunca registrar cartão ou chave; armazenar apenas dados mínimos e senha com algoritmo próprio para senhas.
- **Critério de aceite:** busca no repositório e inspeção dos logs não revelam segredos, cartão ou senha; configuração falha com clareza quando secrets obrigatórios faltam; senhas novas são armazenadas com hash forte e salt.

### [CRITICAL] AUD-002 — Endpoints administrativos e destrutivos sem autenticação/autorização

- **Arquivo e linhas:** `src/app.js:5-10`; `src/AppManager.js:80-80`; `src/AppManager.js:131-136`
- **Categoria:** AP-03 — Autenticação ou autorização inexistente/quebrada
- **Evidência:** apenas `express.json()` é registrado antes das rotas; o relatório administrativo e a exclusão de usuário não possuem middleware ou guard.
- **Descrição:** qualquer cliente com acesso à API pode ler o relatório financeiro e excluir usuários por ID.
- **Impacto:** divulgação de dados financeiros/pessoais e alteração destrutiva não autorizada.
- **Recomendação:** introduzir autenticação verificável e autorização por papel/recurso, aplicadas antes dos handlers administrativos e destrutivos.
- **Critério de aceite:** requisições anônimas recebem `401`, usuários sem privilégio recebem `403` e somente papéis autorizados acessam cada operação, com testes de integração.

### [HIGH] AUD-003 — Algoritmo caseiro e senha default previsível

- **Arquivo e linhas:** `src/utils.js:17-22`; `src/AppManager.js:68-69`
- **Categoria:** AP-07 — Criptografia insegura
- **Evidência:** `badCrypto` repete Base64 e trunca o resultado para dez caracteres; quando `pwd` é ausente usa um default previsível.
- **Descrição:** Base64 não é função de derivação de senha e não há salt nem custo criptográfico adequado.
- **Impacto:** hashes reversíveis/previsíveis permitem recuperação ou quebra rápida de senhas e contas criadas sem senha explícita compartilham credencial conhecida.
- **Recomendação:** exigir senha válida e usar Argon2id, scrypt ou bcrypt por biblioteca mantida, com salt e custo apropriados; planejar rehash de registros existentes.
- **Critério de aceite:** senha ausente é rejeitada; hashes distintos são produzidos para senhas iguais e verificados por biblioteca adequada, sem armazenamento do texto original.

### [HIGH] AUD-004 — AppManager concentra HTTP, persistência e múltiplos domínios

- **Arquivo e linhas:** `src/AppManager.js:4-141`
- **Categoria:** AP-04 — God Class/God Module
- **Evidência:** uma classe cria conexão/schema/seeds, registra três rotas, interpreta requests, processa pagamento, cria usuário/matrícula, gera relatório e exclui dados.
- **Descrição:** a classe possui muitas razões independentes para mudar e não há limites entre routes, controllers/use cases e repositories/models.
- **Impacto:** alto acoplamento, testes isolados difíceis e maior probabilidade de regressões em mudanças de negócio ou infraestrutura.
- **Recomendação:** estabelecer composition root e separar rotas, controllers, services/use cases e repositories por domínio, preservando os contratos HTTP.
- **Critério de aceite:** handlers HTTP apenas adaptam entrada/saída; workflows residem em services; SQL fica encapsulado em repositories; componentes aceitam dependências injetadas.

### [HIGH] AUD-005 — Workflow de checkout implementado diretamente na rota

- **Arquivo e linhas:** `src/AppManager.js:28-78`
- **Categoria:** AP-05 — Regra de negócio em route/controller
- **Evidência:** o callback HTTP decide pagamento pelo cartão, cria usuário, matrícula e pagamento, registra auditoria, atualiza cache e monta a resposta.
- **Descrição:** regras e orquestração do caso de uso estão acopladas a `req`, `res` e callbacks do driver SQLite.
- **Impacto:** regras não são reutilizáveis nem testáveis sem HTTP/banco e mudanças no contrato web podem afetar o domínio.
- **Recomendação:** extrair um caso de uso de checkout com interfaces para repositories, gateway de pagamento, auditoria e cache; manter na rota apenas validação/adaptação HTTP.
- **Critério de aceite:** o checkout pode ser testado sem Express e sem SQLite real, enquanto método, path, status e payloads existentes permanecem cobertos.

### [HIGH] AUD-006 — Checkout multi-etapa sem transação

- **Arquivo e linhas:** `src/AppManager.js:50-71`
- **Categoria:** AP-08 — Operação multi-etapa sem transação
- **Evidência:** criação opcional de usuário, matrícula, pagamento e log ocorre em escritas encadeadas sem `BEGIN`, `COMMIT` ou `ROLLBACK`; erro no log é ignorado.
- **Descrição:** cada escrita confirma independentemente e falhas posteriores não desfazem etapas anteriores.
- **Impacto:** podem existir usuário/matrícula sem pagamento ou checkout sem auditoria, causando corrupção financeira e operacional.
- **Recomendação:** executar todas as mutações do checkout como uma unidade transacional e efetuar rollback em qualquer falha; definir se cache ocorre apenas após commit.
- **Critério de aceite:** falha injetada em cada etapa deixa todas as tabelas no estado anterior e nenhum cache de sucesso é publicado antes do commit.

### [HIGH] AUD-007 — Infraestrutura concreta e cache global mutável

- **Arquivo e linhas:** `src/AppManager.js:5-8`; `src/utils.js:9-15`; `src/app.js:8-10`
- **Categoria:** AP-06 — Acoplamento concreto e estado global mutável
- **Evidência:** `AppManager` instancia diretamente `sqlite3.Database`; `globalCache` é singleton mutável sem limite/expiração; o entry point não injeta abstrações.
- **Descrição:** infraestrutura e estado compartilhado ficam incorporados ao processo e ao caso de uso.
- **Impacto:** isolamento de testes e substituição de banco/cache são difíceis; o cache cresce durante a vida do processo e diverge entre múltiplas instâncias.
- **Recomendação:** criar dependências no composition root, injetar repositories/cache e aplicar política explícita de capacidade, TTL e armazenamento compartilhado quando necessário.
- **Critério de aceite:** services recebem interfaces substituíveis; testes usam doubles; cache possui ciclo de vida e limites definidos, sem singleton exportado.

### [MEDIUM] AUD-008 — Validação insuficiente e tipos de entrada não controlados

- **Arquivo e linhas:** `src/AppManager.js:29-35`; `src/AppManager.js:45-46`; `src/AppManager.js:131-133`
- **Categoria:** AP-10 — Validação ausente ou inconsistente
- **Evidência:** checkout valida apenas truthiness de quatro campos; não valida nome/email/senha, tipo/faixa de `c_id` nem formato do cartão; `:id` é usado sem validar inteiro positivo.
- **Descrição:** a borda HTTP não estabelece um schema consistente antes de dados alcançarem regras e SQL.
- **Impacto:** entradas inválidas geram decisões incorretas, coerção implícita, respostas inconsistentes e dados de baixa qualidade.
- **Recomendação:** definir schemas/DTOs para params e body, rejeitando campos ausentes, tipos/faixas/formato inválidos e aplicando invariantes no domínio.
- **Critério de aceite:** testes de tabela cobrem entradas válidas e inválidas e garantem `400` estável antes de qualquer efeito persistente.

### [MEDIUM] AUD-009 — Erros de banco ignorados ou classificados incorretamente

- **Arquivo e linhas:** `src/AppManager.js:37-41`; `src/AppManager.js:57-61`; `src/AppManager.js:92-106`; `src/AppManager.js:131-136`
- **Categoria:** AP-11 — Tratamento de erros disperso ou silencioso
- **Evidência:** erro ao buscar curso vira `404`; erros de audit log, enrollments, user/payment lookup e delete são ignorados; delete responde sucesso mesmo após falha.
- **Descrição:** callbacks tratam erros de modos diferentes e não há middleware central ou propagação consistente.
- **Impacto:** clientes recebem sucesso/404 indevidos, respostas podem nunca terminar e falhas operacionais ficam invisíveis.
- **Recomendação:** propagar erros específicos a um handler central, distinguir indisponibilidade de ausência e só emitir sucesso após confirmação da operação.
- **Critério de aceite:** falhas injetadas em cada query geram resposta 5xx estável, logging estruturado e exatamente uma finalização de response.

### [MEDIUM] AUD-010 — Relatório financeiro executa consultas N+1 aninhadas

- **Arquivo e linhas:** `src/AppManager.js:83-127`
- **Categoria:** AP-09 — Query N+1
- **Evidência:** após buscar cursos, executa uma query de matrículas por curso e duas queries por matrícula (usuário e pagamento).
- **Descrição:** a quantidade de consultas cresce como `1 + cursos + 2 × matrículas`.
- **Impacto:** latência e carga no banco crescem linearmente com o volume, agravadas pela serialização parcial de callbacks.
- **Recomendação:** usar JOINs/CTEs ou buscas em lote e agregação, preservando exatamente o formato e a semântica do relatório.
- **Critério de aceite:** teste com múltiplos cursos/matrículas confirma o payload e um número constante ou limitado de queries.

### [MEDIUM] AUD-011 — Ausência de integridade referencial produz registros órfãos

- **Arquivo e linhas:** `src/AppManager.js:12-16`; `src/AppManager.js:131-136`
- **Categoria:** AP-16 — Integridade referencial e exclusão inconsistente
- **Evidência:** tabelas usam IDs relacionados sem declarar `FOREIGN KEY`; a exclusão remove apenas `users`, e a própria resposta admite matrículas/pagamentos remanescentes.
- **Descrição:** relacionamentos e política de exclusão não são impostos pelo banco nem tratados atomicamente pela aplicação.
- **Impacto:** relatórios exibem alunos desconhecidos, dados órfãos acumulam e o estado deixa de representar o domínio.
- **Recomendação:** habilitar foreign keys, declarar constraints e escolher política explícita (restrição, cascade ou soft delete) executada transacionalmente.
- **Critério de aceite:** banco rejeita referências inválidas e teste de exclusão comprova a política escolhida sem órfãos.

### [MEDIUM] AUD-012 — Dependência transitiva marcada deprecated no lockfile

- **Arquivo e linhas:** `package-lock.json:2021-2034`; `package-lock.json:2113-2117`
- **Categoria:** AP-12 — API deprecated ou legada
- **Evidência:** `sqlite3` 5.1.7 depende de `tar ^6.1.11`; a versão resolvida `tar` 6.2.1 contém metadado `deprecated` alertando sobre versões antigas e vulnerabilidades conhecidas.
- **Descrição:** o grafo travado inclui pacote oficialmente marcado como não suportado pela própria metadata instalada. Não há import direto de `tar` no código.
- **Impacto:** risco de manutenção e segurança na cadeia de instalação, dependente dos caminhos efetivamente exercidos pelo instalador de `sqlite3`.
- **Recomendação:** avaliar atualização compatível de `sqlite3`/lockfile que elimine a cadeia depreciada e validar com auditoria de dependências; não forçar versão transitiva sem teste.
- **Critério de aceite:** lockfile regenerado por atualização suportada não contém o pacote deprecated e instalação/boot/testes permanecem funcionais.

### [LOW] AUD-013 — Configuração operacional hardcoded

- **Arquivo e linhas:** `src/utils.js:1-7`; `src/app.js:12-13`
- **Categoria:** AP-13 — Configuração hardcoded
- **Evidência:** porta HTTP é literal no módulo utilitário e consumida diretamente no entry point.
- **Descrição:** configuração operacional não pode variar por ambiente sem edição do código. Segredos no mesmo objeto foram tratados separadamente em AUD-001.
- **Impacto:** reduz portabilidade e dificulta execução concorrente/deploy em plataformas que fornecem porta por ambiente.
- **Recomendação:** ler porta de variável de ambiente com validação e default explícito apenas para desenvolvimento.
- **Critério de aceite:** aplicação aceita porta configurada externamente, rejeita valor inválido e documenta o default local.

### [LOW] AUD-014 — Nomenclatura opaca, código morto e callback excessivamente aninhado

- **Arquivo e linhas:** `src/AppManager.js:2-2`; `src/AppManager.js:26-26`; `src/AppManager.js:28-77`; `src/utils.js:10-10`; `src/utils.js:25-25`
- **Categoria:** AP-15 — Nomenclatura e legibilidade deficientes
- **Evidência:** request é copiada para variáveis `u`, `e`, `p`, `cid`, `cc`; `self` alterna com `this`; checkout possui múltiplos níveis de callbacks; `totalRevenue` é importado/exportado mas nunca utilizado.
- **Descrição:** abreviações, import morto e controle assíncrono aninhado ocultam responsabilidades e caminhos de falha.
- **Impacto:** manutenção e revisão ficam mais propensas a erro, especialmente no workflow financeiro.
- **Recomendação:** usar nomes de domínio, remover código morto e decompor o fluxo em funções/casos de uso assíncronos após estabelecer testes de contrato.
- **Critério de aceite:** lint não aponta imports/exports mortos e cada unidade tem responsabilidade/nome claros sem alterar respostas HTTP.

## APIs deprecated ou legadas

- **Dependências verificadas:** `express` declarado como `^4.18.2` e resolvido em 4.22.1; `sqlite3` declarado como `^5.1.6` e resolvido em 5.1.7; APIs usadas: `express()`, `express.json()`, `app.get/post/delete`, `app.listen`, `sqlite3.verbose()`, `Database`, `serialize`, `run`, `get` e `all`.
- **Resultado:** nenhuma depreciação de API diretamente usada foi comprovada pelos manifestos/metadados locais. Foi comprovada a dependência transitiva deprecated `tar` 6.2.1 (AUD-012). Outros pacotes transitivos também possuem marcadores de depreciação, mas foram consolidados e não classificados sem demonstrar impacto direto adicional.
- **Fonte da confirmação:** versões e marcadores `deprecated` do `package-lock.json`; análise dos imports e símbolos no código. A documentação online não foi consultada e nenhuma versão de runtime Node.js é declarada em `engines`.

## Plano recomendado

1. Rotacionar possíveis segredos, remover dados sensíveis dos logs, substituir hashing e proteger endpoints com autenticação/autorização.
2. Criar composition root e separar routes, controllers, services/use cases e repositories por domínio, mantendo contratos HTTP.
3. Tornar checkout e exclusão transacionais, impor integridade referencial e substituir o N+1 do relatório por consulta agregada/em lote.
4. Centralizar validação e erros, externalizar configuração e remover estado/código morto.
5. Antes de editar, capturar baseline de boot/endpoints; depois, validar testes, boot, smoke tests, persistência e reauditar todos os findings.

## Limitações

- As Fases 1 e 2 foram estritamente estáticas: instalação, boot, testes, seed e requisições não foram executados.
- O projeto não declara versão de Node.js, scripts de teste/lint/migration nem possui arquivos de teste identificados.
- Não foi possível determinar estaticamente se os literais sensíveis são credenciais ativas; seus valores foram mascarados e a recomendação é rotacioná-los caso tenham sido usados.
- O banco é `:memory:` e o DDL é criado no boot; não há migrations ou schema separado para validar fora do código.
- A checagem de depreciação limitou-se à versão resolvida, metadados do lockfile e símbolos utilizados; não houve consulta online nem execução para capturar warnings.

## Confirmação

Fase 2 concluída. Deseja prosseguir com a refatoração (Fase 3)? [s/n]

## Validação pós-refatoração

### Nova estrutura

```text
src/
├── app.js                       # composition root / app factory
├── server.js                    # listen e shutdown
├── config/                      # configuração validada
├── controllers/                 # adaptação dos casos de uso à resposta HTTP
├── database/                    # conexão, transação, schema e seed
├── middlewares/                 # autenticação e erros
├── repositories/                # SQL parametrizado por domínio
├── routes/                      # métodos, paths e middleware
├── security/                    # password hasher scrypt
├── services/                    # checkout, relatório, exclusão e gateway
└── validation/                  # DTO/validação da entrada
tests/run.js                     # unidade, integração e contrato HTTP
```

| Finding | Estado | Evidência |
|---|---|---|
| AUD-001 | Corrigido | Segredos removidos; `src/config/index.js:1-14` exige configuração externa; `src/security/passwordHasher.js:4-10` usa scrypt/salt; smoke test não escreveu cartão/chave no log. Rotação de eventual segredo real permanece ação operacional externa. |
| AUD-002 | Corrigido | `src/routes/index.js:5-7` aplica autenticação aos endpoints administrativo/destrutivo; `src/middlewares/adminAuth.js:9-16`; testes `tests/run.js:67-79` comprovam 401, 403 e 200 autorizado. |
| AUD-003 | Corrigido | `src/security/passwordHasher.js:4-10`; seed recebe segredo aleatório em `src/database/initialize.js:11-12`; testes `tests/run.js:58-65` comprovam salt e ausência de texto claro. |
| AUD-004 | Corrigido | `src/app.js:23-51` é composition root; responsabilidades estão distribuídas em `routes/`, `controllers/`, `services/`, `repositories/` e `database/`; `AppManager` foi removido. |
| AUD-005 | Corrigido | Rota apenas faz binding em `src/routes/index.js:3-8`; controller adapta HTTP; workflow está em `src/services/checkoutService.js:6-24`. |
| AUD-006 | Corrigido | Transação com rollback em `src/database/database.js:35-44` e unidade transacional em `src/services/checkoutService.js:13-24`; falha injetada comprova rollback em `tests/run.js:105-117`. |
| AUD-007 | Corrigido | Infraestrutura é criada/injetada somente em `src/app.js:23-44`; cache global foi removido junto com `src/utils.js`. |
| AUD-008 | Corrigido | DTO valida nome, email, senha, curso, cartão e ID em `src/validation/checkoutInput.js:3-24`; entrada inválida retorna 400 em `tests/run.js:81-83`. |
| AUD-009 | Corrigido | Promises rejeitam todos os erros SQLite em `src/database/database.js:8-32`; controllers encaminham falhas; `src/middlewares/errorHandler.js:9-16` centraliza respostas/log. |
| AUD-010 | Corrigido | Uma consulta com JOINs substitui o N+1 em `src/repositories/reportRepository.js:4-13`; agregação ocorre em memória em `src/services/financialReportService.js:4-15`. |
| AUD-011 | Corrigido | Foreign keys e cascades em `src/database/initialize.js:4-9`; exclusão transacional em `src/services/deleteUserService.js:1-4`; teste comprova ausência de órfãos em `tests/run.js:99-102`. |
| AUD-012 | Bloqueado | Registro npm em 2026-08-12 informa `sqlite3` 6.0.1 com `tar ^7.5.10`, mas exige Node `>=20.17.0`; ambiente disponível é Node 14.21.3. Atualizar a major sem upgrade de runtime violaria a baseline. Lockfile permanece com `sqlite3` 5.1.7/`tar` 6.2.1 deprecated. |
| AUD-013 | Corrigido | `src/config/index.js:1-14` lê e valida `PORT`, `ADMIN_API_KEY` e `DATABASE_PATH`; `.env.example` documenta placeholders. |
| AUD-014 | Corrigido | Variáveis opacas, callback hell, import/export morto e módulo utilitário misto foram removidos; nomes e casos de uso estão explícitos em `src/services/checkoutService.js:6-24`. |

### Comandos executados

```text
git status --short
  Alterações preexistentes fora de ecommerce-api-legacy registradas e preservadas.

npm start (baseline, antes da instalação)
  FAIL preexistente: MODULE_NOT_FOUND: express.

npm ci --no-audit
  PASS: 191 pacotes instalados pelo package-lock; warnings de dependências deprecated confirmados.

npm start (baseline com dependências, sandbox padrão)
  BLOCKED pelo ambiente: listen EPERM 0.0.0.0:3000.

npm start (baseline com permissão local) + curl dos três endpoints
  PASS: relatório 200, checkout válido 200, checkout inválido 400, delete 200.
  Log da baseline confirmou exposição de cartão/chave; valores não reproduzidos aqui.

node --check <todos os arquivos JavaScript em src/ e tests/>
  PASS.

git diff --check
  PASS.

npm test
  PASS: 4 grupos — validação, scrypt, contratos/auth/integridade e rollback injetado.

npm view sqlite3 version dependencies --json
npm view sqlite3@6.0.1 engines --json
  PASS: versão atual consultada; upgrade requer Node >=20.17.0.

ADMIN_API_KEY=<mascarado> npm start + smoke tests por curl
  PASS: boot, 401 anônimo, relatório autorizado 200, checkout 200/400 e delete autorizado 200.
```

### Boot e endpoints

| Verificação | Resultado | Evidência |
|---|---|---|
| Boot | PASS | `ADMIN_API_KEY=<mascarado> npm start` exibiu `LMS API rodando na porta 3000...`; encerramento por SIGINT sem erro da aplicação. |
| `POST /api/checkout` válido | PASS | 200, `application/json`, shape `{msg, enrollment_id}` preservado. |
| `POST /api/checkout` inválido | PASS | 400, corpo `Bad Request` preservado. |
| `POST /api/checkout` recusado | PASS | Teste automatizado: 400, corpo `Pagamento recusado` preservado. |
| `GET /api/admin/financial-report` anônimo | PASS | 401 após correção intencional de segurança. |
| `GET /api/admin/financial-report` autorizado | PASS | 200, `application/json`, array com `{course, revenue, students}` preservado. |
| `DELETE /api/users/:id` autorizado | PASS | 200, texto; conteúdo atualizado para não afirmar corrupção, e cascade comprovado por consulta. |
| Rollback do checkout | PASS | Trigger de falha no audit log produziu 500 e contagens de users/enrollments/payments permaneceram na baseline. |

### Achados residuais e limitações

- AUD-012 permanece bloqueado: eliminar a cadeia deprecated exige atualizar o runtime Node 14.21.3 para pelo menos 20.17.0 e então migrar `sqlite3` para a major 6, com nova instalação e matriz completa de validação.
- A rotação de qualquer credencial que tenha sido real é uma ação operacional externa e não pode ser comprovada no repositório.
- O gateway de pagamento continua sendo um simulador local baseado no primeiro dígito do cartão, pois substituir a integração alteraria o escopo e exigiria credenciais/decisão de produto; o cartão não é persistido nem registrado.
- O banco continua em memória por contrato do projeto. Não foram necessárias migrations de dados persistidos.
- A proteção administrativa usa uma chave compartilhada configurada externamente. É adequada à correção incremental deste projeto, mas identidade individual, papéis e trilha por operador exigiriam requisitos de produto adicionais.
