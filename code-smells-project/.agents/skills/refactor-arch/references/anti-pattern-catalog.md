# Catálogo de anti-patterns

## Uso do catálogo

Tratar os sinais como candidatos, nunca como prova isolada. Confirmar contexto, fluxo da entrada até o sink e controles compensatórios. Cada finding precisa de arquivo e linhas, evidência, impacto e recomendação. Aplicar a escala do projeto: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.

## Catálogo obrigatório

### AP-01 — Injeção e execução arbitrária — CRITICAL

- Sinais: SQL, comandos, templates, paths ou código montados com entrada externa; `eval`, `exec`, shell ou query administrativa exposta.
- Confirmar: origem controlada pelo cliente, ausência de parametrização/allowlist e operação alcançável.
- Correção: parametrização, APIs estruturadas, allowlist e remoção de endpoints genéricos.

### AP-02 — Segredos e dados sensíveis expostos — CRITICAL

- Sinais: chaves, tokens, senhas ou credenciais no código; senha em texto puro; logs ou respostas com cartão, senha ou hash.
- Confirmar: distinguir exemplo obviamente fictício de segredo operacional, mas tratar defaults inseguros como risco. Nunca repetir o valor no relatório.
- Correção: rotação, secret manager/ambiente, hashing de senha apropriado, DTOs e redaction de logs.

### AP-03 — Autenticação ou autorização inexistente/quebrada — CRITICAL

- Sinais: tokens previsíveis ou sem validação, rotas administrativas públicas, alteração de role pelo cliente, autenticação sem middleware.
- Confirmar: verificar cadeia de middlewares e guards antes de concluir ausência.
- Correção: autenticação verificável, autorização por recurso/papel e princípio do menor privilégio.

### AP-04 — God Class/God Module — CRITICAL ou HIGH

- Sinais: um arquivo/classe reúne HTTP, banco, múltiplos domínios, regras, notificações e serialização; muitas razões para mudar.
- Usar CRITICAL quando a violação completa de responsabilidades também comprometer funcionamento/segurança; caso contrário HIGH.
- Correção: extrair por domínio e responsabilidade com interfaces claras.

### AP-05 — Regra de negócio em route/controller — HIGH

- Sinais: cálculo complexo, workflow, transação, envio de notificação ou política de domínio dentro de callback/decorator HTTP.
- Correção: route adapta HTTP; controller/use case orquestra; model/domain service mantém invariantes.

### AP-06 — Acoplamento concreto e estado global mutável — HIGH

- Sinais: conexão/cache/sessão global, instanciação direta de infraestrutura dentro de regra, singletons mutáveis e imports circulares.
- Correção: composition root, injeção de dependência, contexto de requisição e interfaces de repository/gateway.

### AP-07 — Criptografia insegura — HIGH

- Sinais: MD5/SHA simples para senha, Base64 como “hash”, algoritmo caseiro, senha default ou comparação insegura.
- Correção: Argon2, scrypt ou bcrypt por biblioteca mantida, salt e custo adequados; migração/rehash.

### AP-08 — Operação multi-etapa sem transação — HIGH ou MEDIUM

- Sinais: várias escritas dependentes seguidas sem transação; commit parcial; rollback ausente.
- Usar HIGH quando puder causar perda financeira ou corrupção importante; MEDIUM para inconsistência limitada.
- Correção: unidade transacional no service/use case e rollback integral.

### AP-09 — Query N+1 — MEDIUM

- Sinais: query/ORM lookup dentro de loops de entidades; carregamento lazy por item; relatório com consultas repetidas.
- Correção: join, eager loading, agregação ou busca em lote. Validar quantidade de queries quando houver instrumentação.

### AP-10 — Validação ausente ou inconsistente — MEDIUM

- Sinais: request usada sem checar tipo/formato/faixa; create e update aplicam regras diferentes; mass assignment.
- Correção: schema/DTO único na borda e invariantes no domínio.

### AP-11 — Tratamento de erros disperso ou silencioso — MEDIUM

- Sinais: `except:`/`catch` genérico, `err` ignorado, detalhes internos devolvidos, sucesso após falha, ausência de rollback.
- Correção: exceções específicas, middleware central, logging estruturado e resposta pública estável.

### AP-12 — API deprecated ou legada — MEDIUM

- Sinais: warning no código/teste, símbolo marcado deprecated na documentação da versão declarada, API em modo legacy ou removida na próxima major.
- Processo obrigatório:
  1. identificar versão no manifesto/lockfile;
  2. localizar símbolos candidatos;
  3. confirmar depreciação na documentação oficial ou metadados instalados daquela versão;
  4. registrar substituto compatível e impacto da migração.
- Exemplos candidatos, não conclusões automáticas: APIs ORM legacy, callbacks substituídos por promises, utilitários removidos ou opções de framework descontinuadas.
- Não classificar apenas porque existe alternativa mais nova.

### AP-13 — Configuração hardcoded — MEDIUM ou LOW

- Sinais: debug, host, porta, caminhos e flags de ambiente no código; regras de negócio como literais espalhados.
- Usar MEDIUM se afetar segurança/operação; LOW para mantenibilidade localizada. Segredos são AP-02.
- Correção: módulo de configuração, ambiente e constantes/políticas nomeadas.

### AP-14 — Duplicação — LOW

- Sinais: serialização, validação, cálculo ou montagem de resposta repetida com pequenas diferenças.
- Correção: extrair somente quando houver conceito compartilhado claro; evitar abstração prematura.

### AP-15 — Nomenclatura e legibilidade deficientes — LOW

- Sinais: abreviações opacas, magic numbers, imports mortos, funções longas e condicionais excessivamente aninhados.
- Correção: nomes orientados ao domínio, constantes, funções menores e remoção de código morto.

### AP-16 — Integridade referencial e exclusão inconsistente — MEDIUM

- Sinais: FKs sem constraints, exclusão deixa órfãos, cascade manual parcial, status/estoque divergentes.
- Correção: constraints, política de cascade explícita e transação.

## Regras de consolidação

- Consolidar ocorrências que compartilham causa e correção; listar todas as localizações relevantes.
- Separar findings quando impactos ou correções forem independentes.
- Não inflar contagem dividindo cada linha repetida em um finding.
- Registrar pelo menos cinco findings quando existirem cinco problemas comprovados; nunca fabricar achados para atingir meta.
- Ordenar CRITICAL → HIGH → MEDIUM → LOW.
