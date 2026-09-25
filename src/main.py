import asyncio
import logging
import os
import signal

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from . import messages
from .database import create_tables, get_solicitacao
from .service import equipe_pode_receber, processar_solicitacao


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logger = logging.getLogger(__name__)


def _nome_solicitante(message) -> str:
    if message.from_user.username:
        return f"@{message.from_user.username}"

    if message.from_user.full_name:
        return message.from_user.full_name

    return str(message.from_user.id)


def _nome_equipe(chamado) -> str:
    if chamado.equipe is not None:
        return chamado.equipe["nome"]

    return chamado.analise.equipe


async def responder(message, texto: str, chamado_id: int):
    try:
        await message.reply_text(texto)
    except Exception as error:
        logger.error(
            "Falha ao enviar a confirmação do chamado #%s para o usuário %s: %s",
            chamado_id,
            message.from_user.id,
            error,
        )


async def encaminhar_chamado(context, chamado, message) -> bool:
    equipe = chamado.equipe

    if not equipe_pode_receber(equipe):
        return False

    try:
        if chamado.analise is not None:
            texto = messages.novo_chamado(
                chamado,
                _nome_solicitante(message),
                equipe["nome"],
            )
        else:
            texto = messages.novo_chamado_sem_analise(
                chamado,
                _nome_solicitante(message),
                equipe["nome"],
            )

        await context.bot.send_message(
            chat_id=equipe["telegram_chat_id"],
            text=texto,
        )
        return True
    except Exception as error:
        logger.error(
            "Falha ao encaminhar o chamado #%s para o grupo da equipe %s: %s",
            chamado.id,
            equipe["nome"],
            error,
        )
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Envie uma solicitação e ela será registrada automaticamente."
    )


async def consultar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Use o comando assim:\n/consultar 1"
        )
        return

    try:
        solicitacao_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "O protocolo precisa ser um número."
        )
        return

    solicitacao = get_solicitacao(solicitacao_id)

    if solicitacao is None:
        await update.message.reply_text(
            "Solicitação não encontrada."
        )
        return

    await update.message.reply_text(messages.consulta(solicitacao))


async def receber_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message is None or message.from_user is None:
        return

    try:
        # A classificação com IA pode demorar (inclui retry em 503). Rodar em
        # thread para não travar o polling do bot enquanto isso.
        chamado = await asyncio.to_thread(
            processar_solicitacao,
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
    if chamado.analise is None and chamado.equipe is None:
        await responder(message, messages.sem_classificacao(chamado.id), chamado.id)
        return

    encaminhado = await encaminhar_chamado(context, chamado, message)

    if chamado.analise is None:
        # Classificação falhou: chamado atribuído por padrão à SUPORTE.
        await responder(
            message,
            messages.sem_classificacao_suporte(
                chamado,
                _nome_equipe(chamado),
                encaminhado,
            ),
            chamado.id,
        )
        return

    await responder(
        message,
        messages.confirmacao(chamado, _nome_equipe(chamado), encaminhado),
        chamado.id,
    )


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

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "A variável TELEGRAM_BOT_TOKEN não foi configurada."
        )

    create_tables()

    # Timeouts maiores que o padrão (5s): a rede que roda o bot já apresentou
    # instabilidade no acesso ao api.telegram.org, causando "Timed out" no
    # envio de respostas mesmo com o serviço funcionando.
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(15)
        .read_timeout(30)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("consultar", consultar)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receber_mensagem,
        )
    )

    print("Bot iniciado.")

    asyncio.run(_rodar_application(application))


async def _rodar_application(application) -> None:
    """Inicializa e mantém o bot rodando até receber SIGINT/SIGTERM.

    O `initialize()` explícito antes do `start()` contorna o erro de startup
    do python-telegram-bot 22.5 (`ExtBot is not properly initialized`), em que
    `start()` acessa `bot.id` antes de o bot ser inicializado.
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


if __name__ == "__main__":
    main()