# Análise de projeto

## Índice

1. Princípios
2. Detecção de stack
3. Detecção de persistência
4. Domínio e arquitetura
5. Inventário reproduzível
6. Contrato da saída

## 1. Princípios

Usar evidência em camadas: manifesto/lockfile, imports, configuração e código executável. Não decidir a stack por extensão isolada. Distinguir dependência declarada de dependência realmente usada.

Não analisar diretórios como `.git`, `.venv`, `venv`, `node_modules`, `vendor`, `dist`, `build`, `coverage`, `__pycache__`, `.pytest_cache`, `.mypy_cache` e bancos gerados.

## 2. Detecção de stack

### Python

- Linguagem: `pyproject.toml`, `requirements*.txt`, `Pipfile`, `poetry.lock` e arquivos `.py`.
- Flask: dependência `flask`, imports `from flask`, criação `Flask(__name__)`, `Blueprint` e decorators `route`.
- Django: `manage.py`, `django` no manifesto, `settings.py`, `urls.py` e classes ORM.
- FastAPI: dependência/import `fastapi`, `FastAPI()` e decorators por método.
- Versão: preferir lockfile ou pin exato; se houver intervalo, informar o intervalo, não uma versão instalada presumida.

### JavaScript/TypeScript

- Linguagem/runtime: `package.json`, lockfile, extensões `.js`, `.mjs`, `.cjs`, `.ts` e campo `engines`.
- Express: dependência `express`, `express()`, `Router()` e chamadas `app.get/post/...`.
- NestJS: dependências `@nestjs/*`, decorators `@Controller` e módulos.
- Fastify: dependência/import `fastify` e registro de plugins/rotas.
- Versão: usar lockfile para versão resolvida e `package.json` para restrição declarada.

### Outras stacks

Aplicar a mesma heurística: manifesto + imports + entry point + padrões de roteamento. Exemplos: Java/Spring (`pom.xml`, `build.gradle`, `@RestController`), Ruby/Rails (`Gemfile`, `config/routes.rb`), PHP/Laravel (`composer.json`, `artisan`) e Go (`go.mod`, handlers HTTP).

## 3. Detecção de persistência

Buscar dependências, URIs, imports, schemas e operações:

- SQLite: `sqlite3`, arquivos `.db`, `sqlite://`.
- SQLAlchemy: `sqlalchemy`, `flask_sqlalchemy`, `db.Model`, `session`.
- Sequelize/TypeORM/Prisma: dependências e schemas próprios.
- PostgreSQL/MySQL: drivers, URLs e configuração, sem imprimir credenciais.
- NoSQL: MongoDB/Mongoose, Redis, DynamoDB ou equivalentes.

Listar tabelas/coleções somente quando confirmadas em schema, migration ou DDL. Mascarar segredos como `***REDACTED***`.

## 4. Domínio e arquitetura

Inferir o domínio a partir de rotas, nomes de entidades, schemas e casos de uso. Descrever capacidades, não apenas substantivos: por exemplo, “LMS com cadastro, matrícula, checkout e relatório financeiro”.

Mapear o fluxo real:

```text
HTTP → route/view → controller/handler → service/use case → model/repository → database
```

Registrar saltos indevidos: route acessando ORM, model formatando HTTP, entry point contendo SQL ou service importando framework web. Classificar a arquitetura observada como monolítica, MVC, layered, modular ou híbrida e justificar com evidência.

## 5. Inventário reproduzível

- Contar arquivos-fonte depois das exclusões.
- Contar linhas físicas e indicar que o valor é aproximado quando houver formatos mistos.
- Identificar entry points por scripts de manifesto, bloco `__main__`, server listen, WSGI/ASGI ou documentação.
- Extrair endpoints de decorators, routers, registro programático e arquivos `.http`.
- Registrar método, path, parâmetros, autenticação aparente e formato de resposta observado no código.
- Identificar comandos existentes de boot, seed, testes, lint e migrations sem executá-los nas Fases 1 e 2.

Comandos de busca são auxiliares; confirmar tudo lendo o contexto. Preferir `rg --files`, `rg -n` e ferramentas nativas do manifesto.

## 6. Contrato da saída

Imprimir:

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão quando comprovada>
Framework:     <framework e versão quando comprovada>
Dependencies:  <dependências arquiteturalmente relevantes>
Domain:        <descrição curta>
Architecture:  <tipo e justificativa curta>
Source files:  <quantidade> files analyzed
Source lines:  ~<quantidade>
Database:      <tecnologia e localização lógica>
DB objects:    <tabelas/coleções confirmadas ou não identificado>
Entry point:   <arquivo/comando identificado>
================================
```

Quando uma informação não puder ser provada, usar `não identificado` e explicar a lacuna; não adivinhar.
