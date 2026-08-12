import sqlite3
import secrets

from flask import current_app, g
from werkzeug.security import generate_password_hash


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL DEFAULT '',
            preco REAL NOT NULL CHECK (preco >= 0),
            estoque INTEGER NOT NULL CHECK (estoque >= 0),
            categoria TEXT NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
            status TEXT NOT NULL DEFAULT 'pendente',
            total REAL NOT NULL CHECK (total >= 0),
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
            produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE RESTRICT,
            quantidade INTEGER NOT NULL CHECK (quantidade > 0),
            preco_unitario REAL NOT NULL CHECK (preco_unitario >= 0)
        );
    """)
    _seed(db)
    _upgrade_plaintext_passwords(db)
    db.commit()


def _seed(db):
    if db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            [
                ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
                ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
                ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
                ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
                ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
                ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
                ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
                ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
                ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
                ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
            ],
        )
    if db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        admin_password = current_app.config.get("SEED_ADMIN_PASSWORD") or secrets.token_urlsafe(24)
        customer_password = current_app.config.get("SEED_CUSTOMER_PASSWORD") or secrets.token_urlsafe(24)
        db.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            [
                ("Admin", "admin@loja.com", generate_password_hash(admin_password), "admin"),
                ("Maria Santos", "maria@email.com", generate_password_hash(customer_password), "cliente"),
            ],
        )


def _upgrade_plaintext_passwords(db):
    rows = db.execute("SELECT id, senha FROM usuarios").fetchall()
    for row in rows:
        if not row["senha"].startswith(("scrypt:", "pbkdf2:")):
            db.execute(
                "UPDATE usuarios SET senha = ? WHERE id = ?",
                (generate_password_hash(row["senha"]), row["id"]),
            )


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
