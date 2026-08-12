# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
python3 seed.py
python3 app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

Configure pelo menos `SECRET_KEY` e as senhas de seed no ambiente. Após o seed, obtenha um token em `POST /login` e envie-o como `Authorization: Bearer <token>`. Endpoints administrativos exigem papel `admin` ou `manager`, conforme a operação.

## Testes

```bash
python3 -m unittest discover -s tests -v
```
