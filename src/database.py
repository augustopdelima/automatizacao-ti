import sqlite3
from pathlib import Path

DATABASE_PATH = Path("/app/data/automation.db")

# Equipes iniciais criadas apenas para demonstração/teste.
# O telegram_chat_id fica vazio (None) de propósito: os IDs reais dos grupos
# devem ser configurados manualmente no banco (ver README).
EQUIPES_INICIAIS_DEMONSTRACAO = [
    {"nome": "SUPORTE", "telegram_chat_id": None},
    {"nome": "INFRAESTRUTURA", "telegram_chat_id": None},
    {"nome": "DESENVOLVIMENTO", "telegram_chat_id": None},
]


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
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
        connection.execute(
            "ALTER TABLE solicitacoes ADD COLUMN resumo TEXT"
        )

    if "equipe_id" not in colunas:
        connection.execute(
            "ALTER TABLE solicitacoes ADD COLUMN equipe_id INTEGER REFERENCES equipes(id)"
        )


def create_tables() -> None:
    with get_connection() as connection:
        _criar_tabela_equipes(connection)
        _inserir_equipes_iniciais(connection)
        _criar_tabela_solicitacoes(connection)
        _migrar_solicitacoes(connection)


def create_solicitacao(
    telegram_user_id: int,
    telegram_username: str | None,
    mensagem: str,
    categoria: str | None = None,
    prioridade: str | None = None,
    resumo: str | None = None,
    equipe_id: int | None = None,
) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO solicitacoes (
                telegram_user_id,
                telegram_username,
                mensagem,
                categoria,
                prioridade,
                resumo,
                equipe_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_user_id,
                telegram_username,
                mensagem,
                categoria,
                prioridade,
                resumo,
                equipe_id,
            ),
        )

        return cursor.lastrowid


def get_solicitacao(solicitacao_id: int):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT s.*, e.nome AS equipe_nome
            FROM solicitacoes s
            LEFT JOIN equipes e ON e.id = s.equipe_id
            WHERE s.id = ?
            """,
            (solicitacao_id,),
        )

        return cursor.fetchone()


def get_equipe_por_nome(nome: str):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT *
            FROM equipes
            WHERE nome = ? COLLATE NOCASE
            """,
            (nome,),
        )

        return cursor.fetchone()


def listar_equipes_ativas() -> list[str]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT nome
            FROM equipes
            WHERE ativa = 1
            ORDER BY nome
            """
        )

        return [row["nome"] for row in cursor.fetchall()]


def atualizar_telegram_chat_id(nome: str, chat_id: str) -> bool:
    """Define o telegram_chat_id de uma equipe cadastrada.

    Retorna True se alguma linha foi atualizada (equipe existente).
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE equipes
            SET telegram_chat_id = ?
            WHERE nome = ? COLLATE NOCASE
            """,
            (chat_id, nome),
        )

        return cursor.rowcount > 0