"""Adapter de IA para o Ollama (modelo local via API HTTP).

Implementa a porta AIProvider. Não conhece regras da aplicação: recebe URL e
modelo na composição e apenas traduz prompts em texto.
"""

import logging

import httpx

from ....application.ports.ai_provider import (
    AIProvider,
    AIResponseError,
    AIUnavailableError,
)

logger = logging.getLogger(__name__)


class OllamaAIProvider:
    """Gera respostas usando o endpoint /api/generate do Ollama."""

    name = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 60.0,
        client: httpx.Client | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        # O client é injetável para testes (httpx.MockTransport); na aplicação
        # a composição cria um real.
        self._client = client if client is not None else httpx.Client(timeout=timeout)

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            # Pede resposta em JSON, o formato que o caso de uso espera.
            "format": "json",
        }

        try:
            resposta = self._client.post(
                f"{self._base_url}/api/generate",
                json=payload,
            )
            resposta.raise_for_status()
        except httpx.HTTPError as error:
            raise AIUnavailableError(
                f"Ollama indisponível em {self._base_url}: {error}"
            ) from error

        try:
            dados = resposta.json()
        except ValueError as error:
            raise AIResponseError("Ollama retornou resposta que não é JSON.") from error

        texto = str(dados.get("response", "")).strip()
        if not texto:
            raise AIResponseError("Ollama retornou resposta vazia.")

        return texto