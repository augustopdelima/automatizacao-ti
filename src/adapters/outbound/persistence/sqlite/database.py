"""Acesso SQLite: conexão e schema (infraestrutura).

Nenhuma regra de negócio vive aqui — apenas lidar com a tecnologia. A
responsabilidade de mapear linhas ↔ entidades fica no repositório.
"""

import sqlite3
from pathlib import Path

EQUIPES_INICIAIS_DEMONSTRACAO = [
    {"nome": "SUPORTE", "telegram_chat_id": None},
    {"nome": "INFRAESTRUTURA", "telegram_chat_id": None},
    {"nome": "DESENVOLVIMENTO", "telegram_chat_id": None},
]


def get_connection(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    return connection


def _criar_tabela_equipes(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS equipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            telegram_chat_id TEXT,
            ativa INTEGER NOT NULL DEFAULT 1
        )
        """
    )


def _inserir_equipes_iniciais(connection: sqlite3.Connection) -> None:
    for equipe in EQUIPES_INICIAIS_DEMONSTRACAO:
        connection.execute(
            """
            INSERT OR IGNORE INTO equipes (nome, telegram_chat_id)
            VALUES (?, ?)
            """,
            (equipe["nome"], equipe["telegram_chat_id"]),
        )


def _criar_tabela_solicitacoes(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS solicitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER NOT NULL,
            telegram_username TEXT,
            mensagem TEXT NOT NULL,
            categoria TEXT,
            prioridade TEXT,
            resumo TEXT,
            equipe_id INTEGER REFERENCES equipes(id),
            status TEXT NOT NULL DEFAULT 'ABERTA',
            criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _migrar_solicitacoes(connection: sqlite3.Connection) -> None:
    """Adiciona colunas novas em bancos criados antes desta feature."""
    colunas = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(solicitacoes)")
    }

    if "resumo" not in colunas:
        connection.execute("ALTER TABLE solicitacoes ADD COLUMN resumo TEXT")

    if "equipe_id" not in colunas:
        connection.execute(
            "ALTER TABLE solicitacoes ADD COLUMN equipe_id INTEGER REFERENCES equipes(id)"
        )


def criar_tabelas(connection: sqlite3.Connection) -> None:
    _criar_tabela_equipes(connection)
    _inserir_equipes_iniciais(connection)
    _criar_tabela_solicitacoes(connection)
    _migrar_solicitacoes(connection)