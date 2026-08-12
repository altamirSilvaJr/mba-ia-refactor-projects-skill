---
name: refactor-arch
description: Auditar e refatorar codebases backend para uma arquitetura MVC preservando comportamento. Usar quando o Codex precisar detectar linguagem, framework, banco e arquitetura; localizar anti-patterns, vulnerabilidades, code smells e APIs deprecated com arquivo e linhas; gerar relatório por severidade; ou, somente após confirmação humana, reorganizar Models, Views/Routes e Controllers e validar boot e endpoints. Aplicável a stacks diferentes, incluindo Python/Flask e Node.js/Express, e a projetos monolíticos ou parcialmente organizados.
---

# Refactor Architecture

Executar as fases abaixo em ordem. Tratar a confirmação entre as fases 2 e 3 como barreira obrigatória. Nunca interpretar a invocação inicial da skill como autorização antecipada para alterar o projeto.

## Regras invariantes

- Trabalhar no projeto corrente e preservar contratos HTTP, dados persistidos e comportamento observável.
- Excluir da análise dependências vendorizadas, ambientes virtuais, builds, caches, cobertura, arquivos gerados, bancos binários e metadados Git.
- Não instalar dependências, executar migrations destrutivas, apagar dados ou alterar arquivos antes da confirmação explícita da Fase 3.
- Fazer achados somente com evidência verificável. Informar arquivo e linha ou intervalo exatos.
- Ordenar achados por `CRITICAL`, `HIGH`, `MEDIUM` e `LOW`; dentro da severidade, ordenar pelo impacto.
- Não afirmar que um problema foi eliminado sem reauditoria e evidência de validação.
- Preservar mudanças preexistentes do usuário e não sobrescrever trabalho fora do escopo.
- Preferir mudanças incrementais e reversíveis. Se a baseline já estiver quebrada, separar falhas preexistentes de regressões.

## Carregamento das referências

Ler cada referência completamente no momento indicado:

- Fase 1: [project-analysis.md](references/project-analysis.md).
- Fase 2: [anti-pattern-catalog.md](references/anti-pattern-catalog.md) e [audit-report-template.md](references/audit-report-template.md).
- Planejamento da Fase 3: [mvc-guidelines.md](references/mvc-guidelines.md) e [refactoring-playbook.md](references/refactoring-playbook.md).
- Validação da Fase 3: [validation-guide.md](references/validation-guide.md).

## Fase 1 — Análise do projeto

1. Ler `references/project-analysis.md` completamente.
2. Confirmar o diretório raiz e inspecionar arquivos de manifesto, lockfiles, configuração, entry points, fontes, schemas/migrations e documentação.
3. Detectar linguagem, runtime, framework, dependências relevantes, persistência e domínio usando múltiplas evidências. Não inferir versão apenas por memória; usar manifestos e lockfiles.
4. Inventariar apenas arquivos-fonte relevantes e contar arquivos e linhas de maneira reproduzível.
5. Mapear entry point, rotas, controllers/handlers, regras de negócio, models/entities, acesso a dados, middlewares e dependências entre camadas.
6. Identificar comandos existentes de instalação, boot, seed, testes e exemplos de requisição sem executá-los nesta fase.
7. Imprimir o bloco `PHASE 1: PROJECT ANALYSIS` definido na referência.
8. Prosseguir automaticamente para a Fase 2, ainda sem modificar arquivos.

## Fase 2 — Auditoria

1. Ler `references/anti-pattern-catalog.md` e `references/audit-report-template.md` completamente.
2. Cruzar o inventário e o código contra todo o catálogo. Usar buscas amplas apenas para localizar candidatos e confirmar cada finding no contexto.
3. Verificar explicitamente APIs deprecated ou legadas na versão realmente declarada pelo projeto. Se não houver evidência, registrar a checagem no escopo, sem inventar finding.
4. Consolidar ocorrências da mesma causa raiz quando a recomendação for única; manter múltiplas localizações na evidência.
5. Para cada finding, registrar ID, título, severidade, arquivo/linhas, evidência, descrição, impacto e recomendação.
6. Gerar o relatório conforme o template e salvá-lo em `reports/` no repositório do desafio. Inferir o nome pelo projeto:
   - `code-smells-project` → `reports/audit-project-1.md`;
   - `ecommerce-api-legacy` → `reports/audit-project-2.md`;
   - `task-manager-api` → `reports/audit-project-3.md`.
   Se o projeto não corresponder a esses nomes, usar `reports/audit-<nome-normalizado>.md` e informar o caminho.
7. Exibir o resumo e o caminho do relatório.
8. Perguntar exatamente: `Fase 2 concluída. Deseja prosseguir com a refatoração (Fase 3)? [s/n]`
9. Encerrar o turno. Não editar código, dependências ou configuração enquanto não houver resposta explícita afirmativa.

Se a resposta for negativa ou ambígua, manter o projeto intacto e oferecer esclarecimentos sobre os achados. Aceitar `s`, `sim`, `y`, `yes` ou uma instrução afirmativa inequívoca como confirmação.

## Fase 3 — Refatoração

Executar somente depois da confirmação explícita posterior ao relatório.

1. Ler `references/mvc-guidelines.md` e `references/refactoring-playbook.md` completamente.
2. Inspecionar `git status` e registrar alterações preexistentes. Não desfazê-las.
3. Ler `references/validation-guide.md` e estabelecer a validação disponível antes de editar: testes existentes, comandos de boot e inventário de endpoints. Se for seguro e permitido, executar baseline agora; se não for possível, declarar a limitação.
4. Criar um plano que mapeie cada finding para uma transformação e uma verificação. Priorizar segurança e preservação de comportamento.
5. Refatorar em incrementos coerentes:
   - extrair configuração e segredos;
   - estabelecer composition root/entry point;
   - separar routes/views, controllers e models/repositories por domínio;
   - mover regras para services/use cases quando não pertencerem a Model ou Controller;
   - centralizar validação e tratamento de erros;
   - corrigir segurança, persistência, performance, duplicação e APIs deprecated;
   - preservar paths, métodos, status e formatos de resposta, salvo correção de exposição insegura documentada.
6. Validar após cada grupo de mudanças. Corrigir regressões causadas pela refatoração antes de continuar.
7. Executar toda a matriz de `references/validation-guide.md`: análise estática disponível, testes, boot real e smoke tests dos endpoints.
8. Reexecutar o catálogo da Fase 2. Marcar cada finding como corrigido, mitigado, aceito ou bloqueado, sempre com evidência.
9. Atualizar o relatório com a seção de validação pós-refatoração sem apagar o estado original da auditoria.
10. Imprimir `PHASE 3: REFACTORING COMPLETE`, nova estrutura, comandos executados, resultados e limitações. Não declarar “zero anti-patterns” se houver achados residuais.

## Condições de parada

- Parar antes de mudanças destrutivas, migrations irreversíveis ou alteração intencional do contrato público e pedir autorização específica.
- Parar se credenciais reais forem encontradas: não reproduzir seus valores; mascarar no relatório e recomendar rotação.
- Parar e explicar se não houver forma segura de preservar comportamento sem uma decisão de produto.
- Considerar a Fase 3 concluída apenas quando a aplicação iniciar e os endpoints originais forem verificados, ou quando uma limitação externa for documentada com os comandos e erros observados.
