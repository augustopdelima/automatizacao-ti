"""Adapter de entrada do Telegram.

Recebe mensagens, converte para o formato da aplicação, chama os casos de uso
e formata as respostas. A lógica de negócio permanece toda fora daqui, nos
casos de uso e no domínio.
"""

import asyncio
import logging
import signal

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ....application.use_cases.consultar_chamado import ConsultarChamadoUseCase
from ....application.use_cases.processar_solicitacao import (
    ProcessarSolicitacaoUseCase,
)
from ....config.settings import Settings
from ....domain.entities import Chamado
from . import messages

logger = logging.getLogger(__name__)


class TelegramBotAdapter:
    """Cobre o transporte do Telegram em torno dos casos de uso."""

    def __init__(
        self,
        settings: Settings,
        processar_solicitacao: ProcessarSolicitacaoUseCase,
        consultar_chamado: ConsultarChamadoUseCase,
    ):
        self._settings = settings
        self._processar = processar_solicitacao
        self._consultar = consultar_chamado

    def run(self) -> None:
        if not self._settings.telegram_bot_token:
            raise RuntimeError(
                "A variável TELEGRAM_BOT_TOKEN não foi configurada."
            )

        # Timeouts maiores que o padrão (5s): a rede que roda o bot já
        # apresentou instabilidade no acesso ao api.telegram.org, causando
        # "Timed out" no envio de respostas mesmo com o serviço funcionando.
        application = (
            Application.builder()
            .token(self._settings.telegram_bot_token)
            .connect_timeout(self._settings.telegram_connect_timeout)
            .read_timeout(self._settings.telegram_read_timeout)
            .build()
        )

        application.add_handler(CommandHandler("start", self._start))
        application.add_handler(CommandHandler("consultar", self._consultar_comando))
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self._receber_mensagem,
            )
        )

        print("Bot iniciado.")

        asyncio.run(self._rodar_application(application))



    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Olá! Envie uma solicitação e ela será registrada automaticamente."
        )

    async def _consultar_comando(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        if not context.args:
            await update.message.reply_text("Use o comando assim:\n/consultar 1")
            return

        try:
            protocolo = int(context.args[0])
        except ValueError:
            await update.message.reply_text("O protocolo precisa ser um número.")
            return

        chamado = self._consultar.executar(protocolo)

        if chamado is None:
            await update.message.reply_text("Solicitação não encontrada.")
            return

        await update.message.reply_text(messages.consulta(chamado))

    async def _receber_mensagem(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        message = update.message

        if message is None or message.from_user is None:
            return

        logger.info("Mensagem recebida do usuário %s", message.from_user.id)

        # Todas as mensagens de texto que chegam aqui foram qualificadas como
        # solicitação de suporte pelo MessageHandler (filters.TEXT & ~COMMAND);
        # comandos (start/consultar) não passam por este fluxo. Avisa
        # imediatamente, antes do processamento demorado (IA/persistência). Se
        # o processamento falhar depois, esta mensagem não é apagada — o
        # usuário recebe a resposta de erro normalmente em seguida.
        await self._responder(message, messages.processing(), None)

        try:
            # A classificação com IA pode demorar (inclui retry em 503). Rodar
            # em thread para não travar o polling do bot enquanto isso.
            chamado = await asyncio.to_thread(
                self._processar.executar,
                mensagem=message.text,
                usuario_id=message.from_user.id,
                usuario_username=message.from_user.username,
            )
        except Exception as error:
            logger.error(
                "Falha ao salvar a solicitação do usuário %s: %s",
                message.from_user.id,
                error,
            )
            await message.reply_text(
                "Ocorreu um erro ao registrar a solicitação. Tente novamente."
            )
            return

        # Classificação falhou e não há equipe padrão (SUPORTE ausente do banco).
        if not chamado.classificado and chamado.equipe is None:
            await self._responder(
                message, messages.sem_classificacao(chamado.id), chamado.id
            )
            return

        encaminhado = await self._encaminhar_chamado(context, chamado, message)

        if not chamado.classificado:
            # Classificação falhou: chamado atribuído por padrão à SUPORTE.
            await self._responder(
                message,
                messages.sem_classificacao_suporte(
                    chamado,
                    self._nome_equipe(chamado),
                    encaminhado,
                ),
                chamado.id,
            )
            return

        await self._responder(
            message,
            messages.confirmacao(
                chamado, self._nome_equipe(chamado), encaminhado
            ),
            chamado.id,
        )


    @staticmethod
    def _nome_solicitante(message) -> str:
        if message.from_user.username:
            return f"@{message.from_user.username}"

        if message.from_user.full_name:
            return message.from_user.full_name

        return str(message.from_user.id)

    @staticmethod
    def _nome_equipe(chamado: Chamado) -> str:
        if chamado.equipe is not None:
            return chamado.equipe.nome

        return chamado.equipe_sugerida or "desconhecida"

    async def _responder(self, message, texto: str, chamado_id: int | None):
        try:
            await message.reply_text(texto)
        except Exception as error:
            logger.error(
                "Falha ao enviar a confirmação do chamado #%s para o usuário %s: %s",
                chamado_id,
                message.from_user.id,
                error,
            )

    async def _encaminhar_chamado(self, context, chamado: Chamado, message) -> bool:
        equipe = chamado.equipe

        if equipe is None or not equipe.pode_receber():
            return False

        try:
            if chamado.classificado:
                texto = messages.novo_chamado(
                    chamado,
                    self._nome_solicitante(message),
                    equipe.nome,
                )
            else:
                texto = messages.novo_chamado_sem_analise(
                    chamado,
                    self._nome_solicitante(message),
                    equipe.nome,
                )

            await context.bot.send_message(
                chat_id=equipe.telegram_chat_id,
                text=texto,
            )
            return True
        except Exception as error:
            logger.error(
                "Falha ao encaminhar o chamado #%s para o grupo da equipe %s: %s",
                chamado.id,
                equipe.nome,
                error,
            )
            return False


    async def _rodar_application(self, application) -> None:
        """Inicializa e mantém o bot rodando até receber SIGINT/SIGTERM.

        O `initialize()` explícito antes do `start()` contorna o erro de
        startup do python-telegram-bot 22.5 (`ExtBot is not properly
        initialized`), em que `start()` acessa `bot.id` antes de o bot ser
        inicializado.
        """
        await application.initialize()
        await application.updater.start_polling()
        await application.start()

        parar = asyncio.Event()
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, parar.set)
        loop.add_signal_handler(signal.SIGTERM, parar.set)

        await parar.wait()

        await application.updater.stop()
        await application.stop()
        await application.shutdown()
