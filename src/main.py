"""Ponto de entrada da aplicação (composition root).

Monta as configurações, os adapters e os casos de uso, e entrega o controle
ao adapter do Telegram. Nenhuma regra de negócio vive aqui.
"""

import logging

from .adapters.inbound.telegram.bot import TelegramBotAdapter
from .application.use_cases.consultar_chamado import ConsultarChamadoUseCase
from .application.use_cases.processar_solicitacao import (
    ProcessarSolicitacaoUseCase,
)
from .config.composition import criar_provider_ia, criar_repositorio
from .config.settings import Settings

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # O httpx loga a URL completa das chamadas, incluindo o token do bot.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # O google-genai emite INFO/WARNING de AFC a cada chamada; avisos que não
    # afetam o funcionamento e só poluem o log.
    logging.getLogger("google_genai.models").setLevel(logging.ERROR)

    settings = Settings.from_env()

    repositorio = criar_repositorio(settings)
    repositorio.criar_tabelas()

    provider_ia = criar_provider_ia(settings)
    logger.info("Provedor de IA configurado: %s", provider_ia.name)

    processar = ProcessarSolicitacaoUseCase(provider_ia, repositorio)
    consultar = ConsultarChamadoUseCase(repositorio)

    bot = TelegramBotAdapter(
        settings=settings,
        processar_solicitacao=processar,
        consultar_chamado=consultar,
    )
    bot.run()


if __name__ == "__main__":
    main()