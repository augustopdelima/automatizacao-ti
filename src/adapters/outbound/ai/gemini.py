"""Adapter de IA para o Google Gemini (API oficial).

Implementa a porta AIProvider. A chave da API é recebida na composição — nunca
fica no código, no README ou em logs. Retry com backoff cobre 503 transitórios
("alta demanda") da API.
"""

import logging
import time

from google import genai

from ....application.ports.ai_provider import (
    AIProvider,
    AIResponseError,
    AIUnavailableError,
)
from ....domain.value_objects import AnaliseSolicitacao

logger = logging.getLogger(__name__)


class GeminiAIProvider:
    """Gera respostas usando a API de geração de conteúdo do Gemini."""

    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        max_tentativas: int = 3,
        intervalo_base: float = 2.0,
        client: genai.Client | None = None,
    ):
        self._model = model
        self._max_tentativas = max_tentativas
        self._intervalo_base = intervalo_base
        # O client é injetável para testes; na aplicação a composição cria um
        # real a partir da chave.
        self._client = client if client is not None else genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        for tentativa in range(1, self._max_tentativas + 1):
            try:
                resposta = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        # Garante que o JSON volte no formato do domínio.
                        "response_schema": AnaliseSolicitacao,
                    },
                )
            except Exception as error:
                if tentativa == self._max_tentativas:
                    raise AIUnavailableError(
                        f"Gemini indisponível após {self._max_tentativas} tentativas."
                    ) from error
                logger.warning(
                    "Gemini indisponível (tentativa %s/%s): %s",
                    tentativa,
                    self._max_tentativas,
                    error,
                )
                time.sleep(self._intervalo_base * tentativa)
                continue
            # Sucesso: sai do laço sem fazer tentativas extras.
            break

        texto = (resposta.text or "").strip()
        if not texto:
            raise AIResponseError("Gemini retornou resposta vazia.")

        return texto