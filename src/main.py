import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .database import create_solicitacao, create_tables, get_solicitacao


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Envie uma solicitação e ela será registrada automaticamente."
    )


async def receber_mensagem(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.message

    if message is None or message.from_user is None:
        return

    solicitacao_id = create_solicitacao(
        telegram_user_id=message.from_user.id,
        telegram_username=message.from_user.username,
        mensagem=message.text,
    )

    await message.reply_text(
        f"Solicitação registrada!\n\n"
        f"Protocolo: #{solicitacao_id}"
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

    await update.message.reply_text(
        f"Solicitação #{solicitacao['id']}\n\n"
        f"Mensagem: {solicitacao['mensagem']}\n"
        f"Status: {solicitacao['status']}\n"
        f"Criada em: {solicitacao['criado_em']}"
    )


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "A variável TELEGRAM_BOT_TOKEN não foi configurada."
        )

    create_tables()

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
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

    application.run_polling()


if __name__ == "__main__":
    main()
