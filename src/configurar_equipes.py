"""Configura os telegram_chat_id das equipes a partir de variáveis de ambiente.

Roda no início do container (ver Dockerfile), antes do bot, para vincular cada
equipe ao grupo do Telegram correspondente. Os IDs dos grupos ficam apenas no
ambiente (.env) e no banco — nunca no código.
"""
import logging
import os

from .database import atualizar_telegram_chat_id, create_tables

logger = logging.getLogger(__name__)

# (variável de ambiente, nome da equipe cadastrada no banco)
EQUIPES_CONFIGURAVEIS = [
    ("EQUIPE_SUPORTE_CHAT_ID", "SUPORTE"),
    ("EQUIPE_INFRAESTRUTURA_CHAT_ID", "INFRAESTRUTURA"),
    ("EQUIPE_DESENVOLVIMENTO_CHAT_ID", "DESENVOLVIMENTO"),
]


def configurar_chat_ids() -> None:
    create_tables()

    for variavel, nome_equipe in EQUIPES_CONFIGURAVEIS:
        chat_id = os.getenv(variavel)

        if not chat_id:
            logger.info(
                "Equipe %s sem telegram_chat_id (variável %s não definida)",
                nome_equipe,
                variavel,
            )
            continue

        if atualizar_telegram_chat_id(nome_equipe, chat_id):
            logger.info("Equipe %s configurada com telegram_chat_id", nome_equipe)
        else:
            logger.warning(
                "Equipe %s não encontrada no banco para aplicar telegram_chat_id",
                nome_equipe,
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    configurar_chat_ids()