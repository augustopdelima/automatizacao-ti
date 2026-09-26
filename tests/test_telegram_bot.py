"""Testes do adapter de entrada do Telegram (fluxo de mensagens).

Usam fakes de Telegram (Update/Message/Context) e os fakes de portas
existentes — nenhum serviço externo (API do Telegram, IA, SQLite real) é
chamado.

Cenários cobertos:
- solicitação de suporte: processing imediato -> processamento -> resposta final;
- mensagem que não é solicitação (comando / sem usuário): sem processing;
- erro no processamento: processing enviado e não apagado, depois mensagem de erro;
- o processing é enviado antes da chamada de IA.
"""

import asyncio
from types import SimpleNamespace

from fakes import FakeAIProvider, FakeRepository
from src.adapters.inbound.telegram import messages
from src.adapters.inbound.telegram.bot import TelegramBotAdapter
from src.application.ports.repository import PersistenceError
from src.application.use_cases.consultar_chamado import ConsultarChamadoUseCase
from src.application.use_cases.processar_solicitacao import (
    ProcessarSolicitacaoUseCase,
)
from src.config.settings import Settings

JSON_VALIDO = (
    '{"categoria": "REDE", "prioridade": "CRITICA", '
    '"resumo": "Internet caiu", "equipe": "INFRAESTRUTURA"}'
)

TEXTO_PROCESSING = messages.processing()


class FakeMessage:
    """Superfície mínima de telegram.Message usada pelos handlers."""

    def __init__(self, text="olá"):
        self.text = text
        self.from_user = SimpleNamespace(id=1, username="ana", full_name="Ana")
        self.respostas = []

    async def reply_text(self, texto: str):
        self.respostas.append(texto)


class FakeUpdate:
    def __init__(self, message=None, args=None):
        self.message = message
        self.args = args or []


class FakeBot:
    def __init__(self):
        self.enviados = []

    async def send_message(self, chat_id, text):
        self.enviados.append((chat_id, text))


class FakeContext(FakeUpdate):
    def __init__(self, args=None):
        super().__init__(args=args)
        self.bot = FakeBot()


def _montar_bot(provider=None, repo=None) -> TelegramBotAdapter:
    repo = repo or FakeRepository()
    provider = provider or FakeAIProvider(resposta=JSON_VALIDO)
    settings = Settings.from_env(
        {"TELEGRAM_BOT_TOKEN": "token", "AI_PROVIDER": "gemini"}
    )
    return TelegramBotAdapter(
        settings=settings,
        processar_solicitacao=ProcessarSolicitacaoUseCase(provider, repo),
        consultar_chamado=ConsultarChamadoUseCase(repo),
    )


def test_solicitacao_envia_processing_antes_da_ia_e_depois_confirmacao():
    eventos: list[str] = []

    class MessageComEventos(FakeMessage):
        async def reply_text(self, texto: str):
            eventos.append(f"reply:{texto}")
            await super().reply_text(texto)

    class ProviderComEventos(FakeAIProvider):
        def generate(self, prompt):
            eventos.append("ia")
            return super().generate(prompt)

    bot = _montar_bot(provider=ProviderComEventos(resposta=JSON_VALIDO))
    update = FakeUpdate(message=MessageComEventos("a internet do laboratório caiu"))
    context = FakeContext()

    asyncio.run(bot._receber_mensagem(update, context))

    # 1ª resposta do Telegram é a de processamento.
    assert eventos[0] == f"reply:{TEXTO_PROCESSING}"
    # A IA só é chamada depois do processing ter sido enviado.
    assert eventos.index(f"reply:{TEXTO_PROCESSING}") < eventos.index("ia")
    # Fluxo normal continua: resposta final com o protocolo.
    resposta_final = update.message.respostas[-1]
    assert "Protocolo: #1" in resposta_final


def test_comando_nao_envia_mensagem_de_processamento():
    bot = _montar_bot()
    update = FakeUpdate(message=FakeMessage())
    context = FakeContext(args=[])

    asyncio.run(bot._start(update, context))
    asyncio.run(bot._consultar_comando(update, context))

    respostas = update.message.respostas
    assert respostas[0] == (
        "Olá! Envie uma solicitação e ela será registrada automaticamente."
    )
    assert respostas[1] == "Use o comando assim:\n/consultar 1"
    assert all(TEXTO_PROCESSING not in resposta for resposta in respostas)


def test_mensagem_sem_usuario_nao_envia_nada():
    bot = _montar_bot()
    update = FakeUpdate(message=FakeMessage())
    update.message.from_user = None

    asyncio.run(bot._receber_mensagem(update, FakeContext()))

    assert update.message.respostas == []


def test_erro_no_processamento_nao_apaga_processing():
    class RepoQueFalha(FakeRepository):
        def salvar_chamado(self, chamado):
            raise PersistenceError("banco indisponível")

    bot = _montar_bot(repo=RepoQueFalha())
    update = FakeUpdate(message=FakeMessage("não consigo logar"))
    context = FakeContext()

    asyncio.run(bot._receber_mensagem(update, context))

    respostas = update.message.respostas
    # Processing enviado e preservado mesmo com falha posterior.
    assert respostas[0] == TEXTO_PROCESSING
    # Mensagem de erro existente, sem detalhes técnicos.
    assert respostas[-1] == (
        "Ocorreu um erro ao registrar a solicitação. Tente novamente."
    )