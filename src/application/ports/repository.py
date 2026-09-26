"""Porta de saída para a persistência.

Casos de uso dependem desta abstração — nunca de sqlite3, SQL ou do banco.
"""

from typing import Protocol

from ...domain.entities import Chamado, Equipe


class PersistenceError(Exception):
    """Falha ao acessar a persistência."""


class AutomationRepository(Protocol):
    """Interface de persistência usada pelos casos de uso."""

    def criar_tabelas(self) -> None:
        """Cria o schema e as equipes iniciais, se ainda não existirem."""
        ...

    def salvar_chamado(self, chamado: Chamado) -> int:
        """Persiste o chamado (sem id) e retorna o protocolo gerado."""
        ...

    def buscar_chamado(self, protocolo: int) -> Chamado | None:
        """Retorna o chamado pelo protocolo, ou None se não existir."""
        ...

    def listar_equipes_ativas(self) -> list[str]:
        """Nomes das equipes ativas (fonte da verdade para o roteamento)."""
        ...

    def buscar_equipe_por_nome(self, nome: str) -> Equipe | None:
        """Retorna a equipe pelo nome (comparação sem diferenciar maiúsculas)."""
        ...

    def atualizar_telegram_chat_id(self, nome: str, telegram_chat_id: str) -> bool:
        """Define o telegram_chat_id de uma equipe.

        Retorna True se alguma linha foi atualizada (equipe existente).
        """
        ...