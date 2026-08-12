# Relatório de Auditoria Arquitetural — code-smells-project

## Metadados

| Campo | Valor |
|---|---|
| Projeto | `code-smells-project` |
| Stack | Python + Flask 3.1.1 + Flask-Cors 5.0.1 + SQLite |
| Arquitetura observada | Monólito modular superficial, com entry point, controllers e acesso a dados separados por arquivo, mas sem limites por domínio ou camada de serviços |
| Escopo | `app.py`, `controllers.py`, `database.py`, `models.py`, `requirements.txt` e documentação; excluídos Git, caches, ambientes, dependências e bancos gerados |
| Arquivos-fonte analisados | 4 |
| Linhas aproximadas | 780 |
| Data | 2026-08-12 |
| Método | Análise estática orientada por evidências |

## Resumo executivo

O projeto implementa uma API de e-commerce para produtos, usuários, autenticação, pedidos, estoque e relatórios. Embora os quatro arquivos sugiram alguma separação, os limites arquiteturais são frágeis: `app.py` contém acesso direto ao banco, `controllers.py` concentra HTTP e regras de múltiplos domínios, e `models.py` reúne queries, serialização e workflows transacionais.

O risco imediato é crítico. Há uma rota pública que executa SQL arbitrário, múltiplas queries vulneráveis a injeção e armazenamento/exposição de senhas em texto puro. A aplicação também mantém chave secreta e debug no código e chega a devolver essa configuração pelo health check.

A prioridade deve ser fechar as superfícies críticas antes da reorganização MVC: remover operações administrativas genéricas, parametrizar queries, proteger credenciais e extrair configuração. Em seguida, separar domínios e responsabilidades, encapsular persistência, corrigir N+1, validar entradas e centralizar erros.

| Severidade | Quantidade |
|---|---:|
| CRITICAL | 4 |
| HIGH | 2 |
| MEDIUM | 4 |
| LOW | 2 |
| **Total** | **12** |

## Arquitetura atual

O fluxo predominante passa por controllers, mas duas rotas administrativas ignoram essa separação e manipulam SQLite diretamente. Não existem services/use cases, repositories por domínio, autenticação/autorização ou middleware central de erros.

```text
HTTP → app.py → controllers.py → models.py → database.py → SQLite
       └──────────────────────────────────────────────→ SQLite
```

Os módulos `controllers.py` e `models.py` atendem simultaneamente produtos, usuários, login, pedidos e relatórios. A conexão SQLite é global e compartilhada por toda a aplicação.

## Findings

### [CRITICAL] AUD-001 — Endpoint público executa SQL arbitrário

- **Arquivo e linhas:** `code-smells-project/app.py:59-78`
- **Categoria:** AP-01 — Injeção e execução arbitrária
- **Evidência:** `POST /admin/query` lê o campo `sql` do JSON e entrega o conteúdo sem restrição a `cursor.execute(query)`. A checagem de prefixo `SELECT` altera somente a resposta; qualquer outra instrução é executada e confirmada.
- **Descrição:** a API transforma entrada remota em comando administrativo de banco sem allowlist, autenticação ou autorização.
- **Impacto:** um cliente pode ler, modificar ou apagar dados e alterar o schema do banco.
- **Recomendação:** remover a rota. Substituir necessidades administrativas por operações predefinidas, autenticadas, autorizadas e auditáveis.
- **Critério de aceite:** a rota deixa de existir ou rejeita SQL livre; nenhuma entrada HTTP alcança uma API genérica de execução de queries.

### [CRITICAL] AUD-002 — SQL Injection em autenticação, escrita e busca

- **Arquivo e linhas:** `code-smells-project/models.py:24-29`, `models.py:43-60`, `models.py:89-110`, `models.py:122-129`, `models.py:133-165`, `models.py:275-280` e `models.py:285-299`
- **Categoria:** AP-01 — Injeção e execução arbitrária
- **Evidência:** identificadores e campos provenientes de requests são concatenados em `SELECT`, `INSERT`, `UPDATE` e `DELETE`; e-mail e senha também são concatenados na query de login.
- **Descrição:** a camada de dados não usa placeholders de maneira consistente e constrói SQL com dados não confiáveis.
- **Impacto:** permite contornar autenticação, extrair dados e corromper produtos, usuários, pedidos ou estoque.
- **Recomendação:** parametrizar todos os valores com a API do `sqlite3`; construir filtros opcionais a partir de cláusulas fixas e uma lista separada de parâmetros.
- **Critério de aceite:** nenhuma query concatena valores externos; testes com aspas e payloads de injeção preservam a semântica esperada.

### [CRITICAL] AUD-003 — Senhas armazenadas em texto puro e devolvidas pela API

- **Arquivo e linhas:** `code-smells-project/database.py:26-34`, `database.py:75-82`, `models.py:72-103` e `models.py:105-129`
- **Categoria:** AP-02 — Segredos e dados sensíveis expostos
- **Evidência:** a tabela usa uma coluna textual `senha`, os seeds inserem senhas legíveis, o login compara texto puro e as consultas/listagens serializam o campo `senha`.
- **Descrição:** não existe password hashing nem DTO que exclua credenciais das respostas.
- **Impacto:** uma consulta à API ou vazamento do banco compromete imediatamente todas as credenciais e pode afetar outros serviços por reutilização de senha.
- **Recomendação:** migrar para hashing próprio para senhas, remover credenciais dos DTOs e definir transição segura para registros existentes.
- **Critério de aceite:** banco não contém senha legível; respostas nunca incluem senha ou hash; autenticação usa verificação de hash.

### [CRITICAL] AUD-004 — Operações administrativas destrutivas não têm controle de acesso

- **Arquivo e linhas:** `code-smells-project/app.py:47-78`
- **Categoria:** AP-03 — Autenticação ou autorização inexistente/quebrada
- **Evidência:** as rotas `/admin/reset-db` e `/admin/query` não registram decorator, middleware, sessão, token, role ou qualquer outra verificação de identidade/permissão.
- **Descrição:** funções administrativas são expostas no mesmo servidor público sem fronteira de autorização.
- **Impacto:** qualquer cliente pode esvaziar integralmente o banco ou executar comandos arbitrários.
- **Recomendação:** remover a execução de SQL e mover manutenção para comando offline; se reset administrativo continuar necessário em ambiente de desenvolvimento, desabilitá-lo por padrão e exigir autorização explícita.
- **Critério de aceite:** usuário anônimo não alcança nenhuma operação administrativa ou destrutiva, e testes cobrem respostas 401/403 quando aplicável.

### [HIGH] AUD-005 — God Modules atravessam domínios e camadas

- **Arquivo e linhas:** `code-smells-project/controllers.py:5-292` e `models.py:4-314`
- **Categoria:** AP-04 — God Class/God Module; AP-05 — Regra de negócio em controller
- **Evidência:** os dois módulos reúnem produtos, usuários, login, pedidos, estoque, notificações, relatórios, health check, serialização e persistência. `criar_pedido` coordena validação de estoque, cálculo, escrita do pedido, itens e baixa de estoque.
- **Descrição:** a separação é por tipo técnico amplo, não por domínio ou caso de uso, e regras relevantes ficam acopladas ao Flask e ao SQLite.
- **Impacto:** baixa coesão, alto acoplamento e testes isolados difíceis; uma mudança de domínio afeta módulos compartilhados extensos.
- **Recomendação:** criar routes/views e controllers por domínio, services/use cases para workflows e repositories para persistência; manter um composition root claro.
- **Critério de aceite:** routes adaptam HTTP, controllers orquestram, services concentram workflows e repositories encapsulam queries, sem dependências HTTP nos models.

### [HIGH] AUD-006 — Conexão global mutável compartilhada entre requisições

- **Arquivo e linhas:** `code-smells-project/database.py:4-11`
- **Categoria:** AP-06 — Acoplamento concreto e estado global mutável
- **Evidência:** `db_connection` é global e reutilizada por todos os chamadores; `check_same_thread=False` desabilita a proteção de thread do driver.
- **Descrição:** ciclo de vida, transações e concorrência da conexão não estão vinculados ao contexto de requisição.
- **Impacto:** requisições podem interferir no mesmo estado transacional, erros podem deixar a conexão inconsistente e testes ficam acoplados a um singleton.
- **Recomendação:** gerenciar conexão por request/app context, fechar no teardown e injetar repositories ou unidade de trabalho nos services.
- **Critério de aceite:** não existe conexão global compartilhada; cada unidade de trabalho tem ciclo de vida e rollback definidos.

### [MEDIUM] AUD-007 — Queries N+1 ao montar pedidos

- **Arquivo e linhas:** `code-smells-project/models.py:171-200` e `models.py:203-233`
- **Categoria:** AP-09 — Query N+1
- **Evidência:** para cada pedido é executada uma query de itens e, dentro do loop de itens, outra query para obter o nome de cada produto.
- **Descrição:** o agregado de pedidos é carregado por consultas encadeadas em loops.
- **Impacto:** a quantidade de queries cresce com pedidos e itens, degradando progressivamente os endpoints de listagem.
- **Recomendação:** usar joins ou consultas em lote para carregar pedidos, itens e produtos em número constante de operações.
- **Critério de aceite:** teste/instrumentação demonstra quantidade de queries constante ou limitada por lote para a listagem.

### [MEDIUM] AUD-008 — Integridade relacional não é imposta pelo banco

- **Arquivo e linhas:** `code-smells-project/database.py:36-52`, `models.py:65-70` e `models.py:133-168`
- **Categoria:** AP-16 — Integridade referencial e exclusão inconsistente
- **Evidência:** `pedidos.usuario_id`, `itens_pedido.pedido_id` e `itens_pedido.produto_id` não possuem constraints `FOREIGN KEY`; a exclusão de produto não trata itens existentes.
- **Descrição:** relações e políticas de exclusão dependem apenas do fluxo da aplicação.
- **Impacto:** exclusões ou falhas podem criar registros órfãos e relatórios inconsistentes.
- **Recomendação:** adicionar chaves estrangeiras e política explícita de `RESTRICT`, `CASCADE` ou soft delete; executar alterações relacionadas em transação.
- **Critério de aceite:** banco rejeita referências inválidas e testes confirmam a política de exclusão escolhida.

### [MEDIUM] AUD-009 — Validação de entrada incompleta e inconsistente

- **Arquivo e linhas:** `code-smells-project/controllers.py:24-54`, `controllers.py:64-92`, `controllers.py:146-176`, `controllers.py:188-206` e `controllers.py:237-245`
- **Categoria:** AP-10 — Validação ausente ou inconsistente
- **Evidência:** criação e atualização de produto aplicam conjuntos diferentes de regras; tipos numéricos são usados antes de validação; e-mail, senha, quantidade e existência do usuário do pedido não são adequadamente validados.
- **Descrição:** cada handler implementa validação manual, sem schema reutilizável nem invariantes centralizadas.
- **Impacto:** payloads malformados geram erros 500, estados inválidos ou comportamento diferente entre create e update.
- **Recomendação:** introduzir schemas/DTOs por operação e manter invariantes essenciais no domínio/service.
- **Critério de aceite:** create/update compartilham regras coerentes e testes de tipos, limites, campos ausentes e referências inválidas retornam 4xx estável.

### [MEDIUM] AUD-010 — Configuração insegura e detalhes internos expostos

- **Arquivo e linhas:** `code-smells-project/app.py:7-9`, `app.py:80-88`, `controllers.py:264-292`
- **Categoria:** AP-02 — Segredos e dados sensíveis expostos; AP-13 — Configuração hardcoded
- **Evidência:** chave secreta e debug estão hardcoded; o servidor inicia com debug em `0.0.0.0`; o health check devolve chave, caminho do banco, ambiente e flag de debug.
- **Descrição:** configuração de ambiente está misturada ao código e informações sensíveis/operacionais são serializadas.
- **Impacto:** exposição de segredo e superfície de diagnóstico em ambiente acessível, além de comportamento inseguro por padrão.
- **Recomendação:** extrair configuração para ambiente, exigir segredo fora de desenvolvimento, desabilitar debug por padrão e reduzir `/health` a dados não sensíveis.
- **Critério de aceite:** nenhum segredo aparece no repositório ou resposta; debug depende de ambiente seguro; health revela somente estado necessário.

### [LOW] AUD-011 — Validação e serialização duplicadas

- **Arquivo e linhas:** `code-smells-project/controllers.py:24-54`, `controllers.py:64-92`, `models.py:4-41`, `models.py:72-103`, `models.py:171-233` e `models.py:285-314`
- **Categoria:** AP-14 — Duplicação
- **Evidência:** create/update repetem extração e validação de produto; produtos, usuários e pedidos são convertidos manualmente em dicionários em diversos pontos.
- **Descrição:** regras e formatos não possuem uma única fonte de verdade.
- **Impacto:** mudanças podem ser aplicadas somente em um fluxo e gerar respostas ou validações divergentes.
- **Recomendação:** criar schemas/DTOs e mapeadores por domínio, extraindo somente conceitos realmente compartilhados.
- **Critério de aceite:** validação e serialização possuem implementação única reutilizada pelos fluxos correspondentes.

### [LOW] AUD-012 — Literais de negócio e logging ad hoc reduzem manutenibilidade

- **Arquivo e linhas:** `code-smells-project/controllers.py:8-12`, `controllers.py:52-54`, `controllers.py:208-210`, `controllers.py:242-250`, `models.py:256-262` e `app.py:83-86`
- **Categoria:** AP-13 — Configuração hardcoded; AP-15 — Nomenclatura e legibilidade deficientes
- **Evidência:** categorias, status, faixas de desconto e mensagens de notificação estão espalhados como literais; operações e erros usam `print` sem estrutura ou correlação.
- **Descrição:** políticas e observabilidade estão embutidas em handlers e funções de persistência.
- **Impacto:** mudanças de regra exigem busca manual e logs são difíceis de consultar ou testar.
- **Recomendação:** nomear constantes/políticas no domínio e usar logging estruturado com níveis, contexto e redaction.
- **Critério de aceite:** regras não ficam duplicadas como literais e logs relevantes usam logger configurado sem dados sensíveis.

## APIs deprecated ou legadas

- **Dependências verificadas:** Flask 3.1.1 e Flask-Cors 5.0.1, conforme `requirements.txt:1-2`.
- **APIs verificadas:** `Flask`, `route`, `add_url_rule`, `request.get_json`, `jsonify`, `app.run` e `flask_cors.CORS`.
- **Resultado:** nenhuma API deprecated foi comprovada no código analisado. Os símbolos Flask utilizados continuam presentes na documentação 3.1; o projeto não usa itens removidos ou marcados como deprecated no changelog 3.x.
- **Fontes da confirmação:** [Flask 3.1 changelog](https://flask.palletsprojects.com/en/stable/changes/), [Flask quickstart 3.1](https://flask.palletsprojects.com/en/stable/quickstart/), [Flask URL rule pattern](https://flask.palletsprojects.com/en/stable/patterns/lazyloading/) e [Flask-Cors API](https://flask-cors.readthedocs.io/en/latest/api.html).

## Plano recomendado

1. Remover `/admin/query`, restringir ou retirar `/admin/reset-db` e eliminar exposição de configuração.
2. Parametrizar SQL, migrar senhas para hashing seguro e remover credenciais das respostas.
3. Criar composition root/config, conexão por contexto e error handler central.
4. Separar produtos, usuários e pedidos em routes, controllers, services e repositories.
5. Introduzir constraints/transações, corrigir N+1 e centralizar schemas/DTOs.
6. Executar testes de caracterização, boot, smoke tests e reauditoria completa.

## Limitações

- A auditoria das Fases 1 e 2 foi estática; dependências não foram instaladas e a aplicação não foi iniciada.
- Não existe suíte de testes no escopo atual, portanto o comportamento em runtime ainda não foi comprovado.
- A natureza real da chave hardcoded não foi verificada; seu valor foi deliberadamente omitido. Por estar versionada e exposta pelo health check, ela foi tratada como configuração sensível insegura.
- O impacto de concorrência da conexão global depende do servidor/runtime, mas o acoplamento e o ciclo de vida compartilhado são confirmados no código.

## Confirmação

Fase 2 concluída. Deseja prosseguir com a refatoração (Fase 3)? [s/n]

## Validação pós-refatoração

Refatoração autorizada em 2026-08-12. O código foi reorganizado em MVC com app factory, configuração, models, repositories, services, controllers, views/routes e middleware central de erros. Os quatro arquivos-fonte originais e aproximadamente 780 linhas foram substituídos por módulos coesos em `src/`; `app.py` permanece como entry point compatível.

### Nova estrutura

```text
code-smells-project/
├── app.py
├── .env.example
├── src/
│   ├── app.py
│   ├── config/settings.py
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── controllers/
│   ├── views/routes/
│   └── middlewares/error_handler.py
└── tests/test_api.py
```

### Estado dos findings

| Finding | Estado | Evidência |
|---|---|---|
| AUD-001 | Corrigido | `src/controllers/admin_controller.py:7-8` desativa SQL remoto; teste e HTTP real confirmaram `POST /admin/query` → 410. |
| AUD-002 | Corrigido | Repositories usam placeholders, por exemplo `src/repositories/product_repository.py:18-63`, `user_repository.py:24-43` e `order_repository.py:12-77`; busca dinâmica concatena somente cláusulas fixas. |
| AUD-003 | Corrigido | `src/repositories/user_repository.py:29-43` usa password hashing e `src/database.py:90-99` migra valores legados; model/DTO de usuário não contém senha. |
| AUD-004 | Corrigido | SQL administrativo foi desativado e reset exige token configurado em `src/services/admin_service.py:4-19`; teste anônimo retorna 403. |
| AUD-005 | Corrigido | Responsabilidades foram separadas em `views/routes`, `controllers`, `services`, `models` e `repositories`, compostas em `src/app.py:27-59`. |
| AUD-006 | Corrigido | `src/database.py:8-21` mantém conexão no contexto Flask `g` e fecha no teardown; não há conexão global compartilhada. |
| AUD-007 | Corrigido | `src/repositories/order_repository.py:50-72` carrega pedidos, itens e produtos em uma única consulta com joins. |
| AUD-008 | Mitigado | Novos bancos recebem FKs e políticas de exclusão em `src/database.py:43-56`, com `PRAGMA foreign_keys` em `database.py:12`. Bancos SQLite já existentes exigem migration de reconstrução das tabelas para incorporar constraints. |
| AUD-009 | Corrigido | Validação foi centralizada em `src/services/product_service.py:35-69`, `user_service.py:23-49` e `order_service.py:11-42`; payload inválido é coberto por teste 400. |
| AUD-010 | Corrigido | `src/config/settings.py:8-19` lê ambiente, gera segredo efêmero seguro quando ausente, desabilita debug e restringe host/CORS por padrão; health não devolve segredo ou path. |
| AUD-011 | Corrigido | Models centralizam serialização e services centralizam validação; controllers e routes apenas orquestram/adaptam HTTP. |
| AUD-012 | Corrigido | Categorias/status possuem constantes nomeadas nos services; prints foram removidos e erros usam logging central em `src/middlewares/error_handler.py:1-25`. |

**Resultado:** 11 corrigidos, 1 mitigado, 0 aceitos e 0 bloqueados. Não foi declarado “zero anti-patterns” porque bancos legados ainda precisam de migration específica para constraints.

### Comandos executados

```text
python -m compileall -q app.py src tests
Resultado: PASS

python -m unittest discover -s tests -v
Resultado: PASS — 6 testes

APP_DATABASE_PATH=/tmp/refactor-arch-project1-boot.db \
APP_PORT=5051 APP_HOST=127.0.0.1 python app.py
Resultado: PASS — servidor iniciou com debug off em http://127.0.0.1:5051
```

As dependências foram instaladas exclusivamente em `/tmp/refactor-arch-project1-venv`; nenhum ambiente virtual ou dependência vendorizada foi adicionado ao repositório.

### Boot e endpoints

| Verificação | Resultado | Evidência |
|---|---|---|
| Boot | PASS | Flask iniciou com debug desligado e sem traceback. |
| `GET /` | PASS | HTTP 200. |
| `GET /health` | PASS | HTTP 200, sem configuração sensível. |
| `GET /produtos` | PASS | HTTP 200. |
| `GET /usuarios/1` | PASS | HTTP 200, sem senha/hash. |
| `POST /pedidos` | PASS | HTTP 201 em banco temporário. |
| `GET /pedidos` | PASS | HTTP 200 após criação. |
| `GET /relatorios/vendas` | PASS | HTTP 200. |
| `POST /admin/query` | PASS | HTTP 410; payload SQL não executado. |

As 19 combinações de método/path da baseline continuam registradas. Os nomes internos dos parâmetros Flask foram modernizados, sem alteração dos paths públicos.

### Testes automatizados

- Leitura de root, health, coleções, recursos por ID, pedidos de usuário e relatório.
- CRUD e busca de produtos.
- Rejeição de produto inválido.
- Criação e login de usuário, hashing e ausência de senha na serialização.
- Criação, listagem e atualização de pedido.
- Bloqueio das superfícies administrativas inseguras.

### Achados residuais e limitações

- Instalações SQLite já existentes precisam de uma migration explícita para reconstruir tabelas com as novas foreign keys; novas bases já nascem com as constraints.
- O servidor validado é o servidor de desenvolvimento do Flask. Deploy de produção deve usar servidor WSGI apropriado.
- A alteração intencional de segurança mantém `/admin/query` reconhecível, mas responde 410; `/admin/reset-db` responde 403 sem token configurado.
