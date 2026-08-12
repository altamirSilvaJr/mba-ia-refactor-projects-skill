# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

Copie as variáveis necessárias de `.env.example` para o ambiente. Em produção, defina obrigatoriamente `APP_SECRET_KEY`; por segurança, debug é desabilitado por padrão e o servidor escuta apenas em `127.0.0.1`.

As senhas dos usuários de demonstração podem ser definidas por `APP_SEED_ADMIN_PASSWORD` e `APP_SEED_CUSTOMER_PASSWORD`. Quando omitidas, são geradas aleatoriamente e não são exibidas; crie outro usuário pela API para testar login.

O endpoint legado `/admin/query` permanece apenas para responder `410 Gone`; execução remota de SQL foi removida. `/admin/reset-db` exige que `APP_ADMIN_TOKEN` esteja configurado e seja enviado no header `X-Admin-Token`.

## Testes

```bash
python -m unittest discover -s tests -v
```
