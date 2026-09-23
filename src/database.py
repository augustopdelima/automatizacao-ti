import sqlite3
from pathlib import Path

DATABASE_PATH = Path("/app/data/automation.db")


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def create_tables() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS solicitacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL,
                telegram_username TEXT,
                mensagem TEXT NOT NULL,
                categoria TEXT,
                prioridade TEXT,
                status TEXT NOT NULL DEFAULT 'ABERTA',
                criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def create_solicitacao(
    telegram_user_id: int,
    telegram_username: str | None,
    mensagem: str,
) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO solicitacoes (
                telegram_user_id,
                telegram_username,
                mensagem
            )
            VALUES (?, ?, ?)
            """,
            (
                telegram_user_id,
                telegram_username,
                mensagem,
            ),
        )

        return cursor.lastrowid


def get_solicitacao(solicitacao_id: int):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT *
            FROM solicitacoes
            WHERE id = ?
            """,
            (solicitacao_id,),
        )

        return cursor.fetchone()
