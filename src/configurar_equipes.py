"""Configura os telegram_chat_id das equipes a partir das variáveis de ambiente.

Roda no início do container (ver Dockerfile), antes do bot, para vincular cada
equipe ao grupo do Telegram correspondente. Os IDs dos grupos ficam apenas no
ambiente (.env) e no banco — nunca no código.

Este script é infraestrutura/composição: usa o repositório via porta, não
acessa SQLite diretamente.
"""

import logging

from .config.composition import criar_repositorio
from .config.settings import Settings

logger = logging.getLogger(__name__)

# (atributo do Settings, variável de ambiente, nome da equipe no banco)
EQUIPES_CONFIGURAVEIS = [
    ("equipe_suporte_chat_id", "EQUIPE_SUPORTE_CHAT_ID", "SUPORTE"),
    (
        "equipe_infraestrutura_chat_id",
        "EQUIPE_INFRAESTRUTURA_CHAT_ID",
        "INFRAESTRUTURA",
    ),
    (
        "equipe_desenvolvimento_chat_id",
        "EQUIPE_DESENVOLVIMENTO_CHAT_ID",
        "DESENVOLVIMENTO",
    ),
]


def configurar_chat_ids() -> None:
    settings = Settings.from_env()
    repositorio = criar_repositorio(settings)
    repositorio.criar_tabelas()

    for atributo, variavel, nome_equipe in EQUIPES_CONFIGURAVEIS:
        chat_id = getattr(settings, atributo)

        if not chat_id:
            logger.info(
                "Equipe %s sem telegram_chat_id (variável %s não definida)",
                nome_equipe,
                variavel,
            )
            continue

        if repositorio.atualizar_telegram_chat_id(nome_equipe, chat_id):
            logger.info("Equipe %s configurada com telegram_chat_id", nome_equipe)
        else:
            logger.warning(
                "Equipe %s não encontrada no banco para aplicar telegram_chat_id",
                nome_equipe,
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    configurar_chat_ids()