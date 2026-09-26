"""Testes do adapter GeminiAIProvider (com client fake, sem chamar a API)."""

from types import SimpleNamespace

import pytest

from src.adapters.outbound.ai.gemini import GeminiAIProvider
from src.application.ports.ai_provider import AIResponseError, AIUnavailableError


class FakeGeminiClient:
    """Client fake com a mesma superfície usada pelo provider."""

    def __init__(self, texto=None, erro=None):
        self.texto = texto
        self.erro = erro
        self.chamadas = []

    @property
    def models(self):
        return self

    def generate_content(self, model=None, contents=None, config=None):
        self.chamadas.append({"model": model, "contents": contents, "config": config})
        if self.erro is not None:
            raise self.erro
        return SimpleNamespace(text=self.texto)


def _provider(client, **kwargs):
    return GeminiAIProvider(
        api_key="chave-teste",
        model="gemini-3.8-flash",
        client=client,
        **kwargs,
    )


def test_generate_sucesso():
    client = FakeGeminiClient(texto='{"categoria": "REDE"}')
    provider = _provider(client)

    resposta = provider.generate("prompt")

    assert resposta == '{"categoria": "REDE"}'
    chamada = client.chamadas[0]
    assert chamada["model"] == "gemini-3.8-flash"
    assert chamada["contents"] == "prompt"
    assert chamada["config"]["response_mime_type"] == "application/json"


def test_resposta_vazia_gera_erro():
    client = FakeGeminiClient(texto="   ")
    provider = _provider(client)

    with pytest.raises(AIResponseError):
        provider.generate("prompt")


def test_falha_repetida_gera_indisponivel():
    client = FakeGeminiClient(erro=RuntimeError("503 alta demanda"))
    provider = _provider(client, max_tentativas=3, intervalo_base=0)

    with pytest.raises(AIUnavailableError):
        provider.generate("prompt")

    assert len(client.chamadas) == 3


def test_sucesso_depois_de_falha():
    class FlakyClient:
        def __init__(self):
            self.chamadas = []

        @property
        def models(self):
            return self

        def generate_content(self, model=None, contents=None, config=None):
            self.chamadas.append(1)
            if len(self.chamadas) == 1:
                raise RuntimeError("503 temporário")
            return SimpleNamespace(text='{"categoria": "REDE"}')

    client = FlakyClient()
    provider = _provider(client, max_tentativas=3, intervalo_base=0)

    resposta = provider.generate("prompt")

    assert "REDE" in resposta
    assert len(client.chamadas) == 2