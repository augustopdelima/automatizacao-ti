"""Testes do adapter OllamaAIProvider (sem serviço externo: MockTransport)."""

import json

import httpx
import pytest

from src.adapters.outbound.ai.ollama import OllamaAIProvider
from src.application.ports.ai_provider import AIResponseError, AIUnavailableError


def _provider(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OllamaAIProvider(
        base_url="http://ollama:11434",
        model="gemma4:12b",
        client=client,
    )


def test_generate_sucesso():
    def handler(request):
        assert request.url.path == "/api/generate"
        payload = json.loads(request.content)
        assert payload["model"] == "gemma4:12b"
        assert payload["stream"] is False
        assert payload["format"] == "json"
        return httpx.Response(
            200,
            json={"response": '{"categoria": "REDE", "prioridade": "ALTA"}'},
        )

    provider = _provider(handler)
    resposta = provider.generate("prompt de teste")

    assert "categoria" in resposta
    assert "REDE" in resposta


def test_resposta_vazia_gera_erro():
    provider = _provider(lambda request: httpx.Response(200, json={"response": "  "}))

    with pytest.raises(AIResponseError):
        provider.generate("prompt")


def test_resposta_nao_json_gera_erro():
    provider = _provider(lambda request: httpx.Response(200, text="erro crasso"))

    with pytest.raises(AIResponseError):
        provider.generate("prompt")


def test_http_503_vira_indisponivel():
    provider = _provider(
        lambda request: httpx.Response(503, json={"error": "overloaded"})
    )

    with pytest.raises(AIUnavailableError):
        provider.generate("prompt")


def test_erro_de_conexao_vira_indisponivel():
    def handler(request):
        raise httpx.ConnectError("conexão recusada")

    provider = _provider(handler)

    with pytest.raises(AIUnavailableError):
        provider.generate("prompt")