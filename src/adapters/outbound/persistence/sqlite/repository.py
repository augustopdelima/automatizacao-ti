"""Implementação da porta AutomationRepository em SQLite.

Converte erros de sqlite3 em PersistenceError para que a aplicação nunca
dependa de exceções específicas do banco.
"""

import logging
import sqlite3
from pathlib import Path

from .....application.ports.repository import PersistenceError
from .....domain.entities import Chamado, Equipe
from .database import criar_tabelas, get_connection

logger = logging.getLogger(__name__)


class SQLiteAutomationRepository:
    """Persistência dos chamados e equipes usando SQLite.

    Recebe o caminho do banco na composição (configurável via DATABASE_PATH).
    """

    def __init__(self, database_path: Path):
        self._database_path = database_path

    def criar_tabelas(self) -> None:
        try:
            with self._conectar() as connection:
                criar_tabelas(connection)
        except sqlite3.Error as error:
            raise PersistenceError(f"Falha ao criar tabelas: {error}") from error

    def salvar_chamado(self, chamado: Chamado) -> int:
        try:
            with self._conectar() as connection:
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
                        chamado.usuario_id,
                        chamado.usuario_username,
                        chamado.mensagem,
                        chamado.categoria,
                        chamado.prioridade,
                        chamado.resumo,
                        chamado.equipe.id if chamado.equipe is not None else None,
                    ),
                )
                protocolo = cursor.lastrowid

            logger.info("Chamado #%s registrado e persistido", protocolo)
            return protocolo
        except sqlite3.Error as error:
            raise PersistenceError(f"Falha ao salvar chamado: {error}") from error

    def buscar_chamado(self, protocolo: int) -> Chamado | None:
        try:
            with self._conectar() as connection:
                linha = connection.execute(
                    """
                    SELECT
                        s.id,
                        s.telegram_user_id,
                        s.telegram_username,
                        s.mensagem,
                        s.categoria,
                        s.prioridade,
                        s.resumo,
                        s.status,
                        s.criado_em,
                        e.id AS equipe_id,
                        e.nome AS equipe_nome,
                        e.telegram_chat_id AS equipe_telegram_chat_id,
                        e.ativa AS equipe_ativa
                    FROM solicitacoes s
                    LEFT JOIN equipes e ON e.id = s.equipe_id
                    WHERE s.id = ?
                    """,
                    (protocolo,),
                ).fetchone()
        except sqlite3.Error as error:
            raise PersistenceError(f"Falha ao buscar chamado: {error}") from error

        if linha is None:
            return None

        return Chamado(
            id=linha["id"],
            mensagem=linha["mensagem"],
            usuario_id=linha["telegram_user_id"],
            usuario_username=linha["telegram_username"],
            categoria=linha["categoria"],
            prioridade=linha["prioridade"],
            resumo=linha["resumo"],
            equipe_sugerida=None,
            equipe=_equipe_da_linha(linha),
            status=linha["status"],
            criado_em=linha["criado_em"],
        )

    def listar_equipes_ativas(self) -> list[str]:
        try:
            with self._conectar() as connection:
                linhas = connection.execute(
                    """
                    SELECT nome
                    FROM equipes
                    WHERE ativa = 1
                    ORDER BY nome
                    """
                ).fetchall()
        except sqlite3.Error as error:
            raise PersistenceError(f"Falha ao listar equipes: {error}") from error

        return [linha["nome"] for linha in linhas]

    def buscar_equipe_por_nome(self, nome: str) -> Equipe | None:
        try:
            with self._conectar() as connection:
                linha = connection.execute(
                    """
                    SELECT
                        id AS equipe_id,
                        nome AS equipe_nome,
                        telegram_chat_id AS equipe_telegram_chat_id,
                        ativa AS equipe_ativa
                    FROM equipes
                    WHERE nome = ? COLLATE NOCASE
                    """,
                    (nome,),
                ).fetchone()
        except sqlite3.Error as error:
            raise PersistenceError(f"Falha ao buscar equipe: {error}") from error

        if linha is None:
            return None

        return _equipe_da_linha(linha)

    def atualizar_telegram_chat_id(self, nome: str, telegram_chat_id: str) -> bool:
        """Define o telegram_chat_id de uma equipe cadastrada.

        Retorna True se alguma linha foi atualizada (equipe existente).
        """
        try:
            with self._conectar() as connection:
                cursor = connection.execute(
                    """
                    UPDATE equipes
                    SET telegram_chat_id = ?
                    WHERE nome = ? COLLATE NOCASE
                    """,
                    (telegram_chat_id, nome),
                )
        except sqlite3.Error as error:
            raise PersistenceError(
                f"Falha ao atualizar telegram_chat_id: {error}"
            ) from error

        return cursor.rowcount > 0

    def _conectar(self) -> sqlite3.Connection:
        try:
            return get_connection(self._database_path)
        except sqlite3.Error as error:
            raise PersistenceError(f"Falha ao conectar no banco: {error}") from error


def _equipe_da_linha(linha: sqlite3.Row) -> Equipe | None:
    if linha["equipe_id"] is None:
        return None

    return Equipe(
        id=linha["equipe_id"],
        nome=linha["equipe_nome"],
        telegram_chat_id=linha["equipe_telegram_chat_id"],
        ativa=bool(linha["equipe_ativa"]),
    )