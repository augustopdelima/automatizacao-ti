"""Fluxo de processamento de um chamado: classificação, equipe e persistência."""
import logging
import sqlite3
from dataclasses import dataclass

from .ai import AnaliseSolicitacao, analisar_solicitacao
from .database import (
    create_solicitacao,
    get_equipe_por_nome,
    listar_equipes_ativas,
)

logger = logging.getLogger(__name__)


@dataclass
class Chamado:
    """Chamado classificado e persistido, pronto para ser notificado."""

    id: int
    mensagem: str
    analise: AnaliseSolicitacao | None
    equipe: sqlite3.Row | None


def equipe_pode_receber(equipe) -> bool:
    """A equipe existe, está ativa e possui grupo configurado no Telegram."""
    return (
        equipe is not None
        and bool(equipe["ativa"])
        and bool(equipe["telegram_chat_id"])
    )


def _motivo_sem_encaminhamento(equipe, analise: AnaliseSolicitacao) -> str:
    if equipe is None:
        return f"equipe '{analise.equipe}' não cadastrada no banco"

    if not equipe["ativa"]:
        return f"equipe '{equipe['nome']}' está inativa"

    if not equipe["telegram_chat_id"]:
        return f"equipe '{equipe['nome']}' não possui telegram_chat_id configurado"

    return "motivo desconhecido"


def processar_solicitacao(
    mensagem: str,
    usuario_id: int,
    usuario_username: str | None,
) -> Chamado:
    """Classifica a mensagem com a IA, valida a equipe e persiste o chamado.

    Se a classificação falhar (analise=None), o chamado é salvo e atribuído
    por padrão à equipe SUPORTE, quando ela existir no banco.
    """
    try:
        analise = analisar_solicitacao(mensagem, listar_equipes_ativas())
    except Exception as error:
        logger.error(
            "Falha ao classificar a solicitação do usuário %s: %s",
            usuario_id,
            error,
        )
        analise = None

    if analise is not None:
        equipe = get_equipe_por_nome(analise.equipe)
    else:
        # Classificação falhou: atribui o chamado à equipe SUPORTE por padrão,
        # quando ela existir no banco (criada no primeiro start).
        equipe = get_equipe_por_nome("SUPORTE")

    chamado_id = create_solicitacao(
        telegram_user_id=usuario_id,
        telegram_username=usuario_username,
        mensagem=mensagem,
        categoria=analise.categoria if analise else None,
        prioridade=analise.prioridade if analise else None,
        resumo=analise.resumo if analise else None,
        equipe_id=equipe["id"] if equipe is not None else None,
    )

    if analise and not equipe_pode_receber(equipe):
        logger.warning(
            "Chamado #%s salvo sem encaminhamento: %s",
            chamado_id,
            _motivo_sem_encaminhamento(equipe, analise),
        )

    return Chamado(
        id=chamado_id,
        mensagem=mensagem,
        analise=analise,
        equipe=equipe,
    )