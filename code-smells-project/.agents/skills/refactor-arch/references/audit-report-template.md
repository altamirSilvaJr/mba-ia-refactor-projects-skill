# Template do relatório de auditoria

Usar esta estrutura no arquivo Markdown. Substituir todos os placeholders e remover instruções entre comentários.

````markdown
# Relatório de Auditoria Arquitetural — <projeto>

## Metadados

| Campo | Valor |
|---|---|
| Projeto | `<nome>` |
| Stack | `<linguagem + framework + persistência>` |
| Arquitetura observada | `<descrição>` |
| Escopo | `<diretórios/arquivos incluídos e exclusões>` |
| Arquivos analisados | `<n>` |
| Linhas aproximadas | `<n>` |
| Data | `<AAAA-MM-DD>` |
| Método | Análise estática orientada por evidências |

## Resumo executivo

<dois a quatro parágrafos sobre risco, arquitetura e prioridades>

| Severidade | Quantidade |
|---|---:|
| CRITICAL | <n> |
| HIGH | <n> |
| MEDIUM | <n> |
| LOW | <n> |
| **Total** | **<n>** |

## Arquitetura atual

<fluxo textual e responsabilidades observadas>

```text
<componente> → <componente> → <componente>
```

## Findings

### [CRITICAL] AUD-001 — <título>

- **Arquivo e linhas:** `<path>:<início>-<fim>`
- **Categoria:** `<anti-pattern do catálogo>`
- **Evidência:** <o que o código faz; mascarar segredos>
- **Descrição:** <causa raiz>
- **Impacto:** <efeito concreto>
- **Recomendação:** <ação verificável>
- **Critério de aceite:** <como comprovar correção>

<!-- Repetir em ordem CRITICAL, HIGH, MEDIUM, LOW. -->

## APIs deprecated ou legadas

- **Dependências verificadas:** <nomes e versões/intervalos>
- **Resultado:** <findings relacionados ou “nenhuma depreciação comprovada no escopo”>
- **Fonte da confirmação:** <documentação/metadado/warning, quando aplicável>

## Plano recomendado

1. <segurança e riscos críticos>
2. <limites arquiteturais>
3. <persistência e performance>
4. <qualidade e limpeza>
5. <validação>

## Limitações

- <aspectos não verificáveis estaticamente, dependências indisponíveis ou baseline ausente>

## Confirmação

Fase 2 concluída. Deseja prosseguir com a refatoração (Fase 3)? [s/n]
````

## Regras de preenchimento

- IDs devem ser estáveis dentro do relatório: `AUD-001`, `AUD-002`, etc.
- Caminhos devem ser relativos ao repositório; linhas são 1-based e devem apontar para a evidência.
- Não incluir valor de segredo, token, senha, cartão ou dado pessoal desnecessário.
- Distinguir “confirmado no código” de inferência e de risco dependente de runtime.
- O resumo numérico deve corresponder ao número real de headings de findings.
- Não declarar validação funcional na Fase 2.

## Atualização pós-refatoração

Na Fase 3, acrescentar ao final sem reescrever o estado original:

````markdown
## Validação pós-refatoração

| Finding | Estado | Evidência |
|---|---|---|
| AUD-001 | Corrigido/Mitigado/Aceito/Bloqueado | `<arquivo:linha ou comando>` |

### Comandos executados

```text
<comando e resultado resumido>
```

### Boot e endpoints

| Verificação | Resultado | Evidência |
|---|---|---|
| Boot | PASS/FAIL/BLOCKED | <log resumido> |
| `<METHOD path>` | PASS/FAIL/BLOCKED | <status/asserção> |

### Achados residuais e limitações

<lista honesta; não usar “zero anti-patterns” sem reauditoria completa>
````
