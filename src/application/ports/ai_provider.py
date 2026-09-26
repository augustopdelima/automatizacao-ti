"""Porta de saída para provedores de IA.

Casos de uso conhecem apenas esta abstração — nunca Ollama, Gemini ou outra
tecnologia concreta.
"""

from typing import Protocol


class AIProviderError(Exception):
    """Erro genérico ao usar um provedor de IA."""


class AIUnavailableError(AIProviderError):
    """O provedor não está disponível (offline, timeout, chave inválida)."""


class AIResponseError(AIProviderError):
    """O provedor respondeu, mas o conteúdo é inválido ou vazio."""


class AIProvider(Protocol):
    """Gera texto a partir de um prompt.

    ``name`` identifica o provedor em logs. A implementação é responsável por
    converter erros de infraestrutura em :class:`AIProviderError`.
    """

    name: str

    def generate(self, prompt: str) -> str:
        """Gera a resposta de texto para o prompt."""
        ...