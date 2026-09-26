"""Composição da aplicação: escolhe e constrói os adapters de infraestrutura.

Este é o único ponto do sistema que conhece a relação variável de ambiente
(settings) → adapter concreto. Casos de uso e domínio nunca veem Ollama ou
Gemini: recebem apenas as portas.
"""

from ..adapters.outbound.ai.gemini import GeminiAIProvider
from ..adapters.outbound.ai.ollama import OllamaAIProvider
from ..adapters.outbound.persistence.sqlite.repository import (
    SQLiteAutomationRepository,
)
from ..application.ports.ai_provider import AIProvider
from ..application.ports.repository import AutomationRepository
from .settings import ConfigurationError, Settings


def criar_repositorio(settings: Settings) -> AutomationRepository:
    """Constrói a persistência a partir do DATABASE_PATH configurado."""
    return SQLiteAutomationRepository(settings.database_path)


def criar_provider_ia(settings: Settings) -> AIProvider:
    """Constrói o provedor de IA escolhido em AI_PROVIDER.

    A decisão ollama vs gemini existe APENAS aqui: trocar a variável de
    ambiente não exige nenhuma alteração nos casos de uso.
    """
    if settings.ai_provider == "ollama":
        if not settings.ollama_model:
            raise ConfigurationError(
                "AI_PROVIDER=ollama exige OLLAMA_MODEL configurado."
            )
        return OllamaAIProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )

    if settings.ai_provider == "gemini":
        if not settings.gemini_api_key:
            raise ConfigurationError(
                "AI_PROVIDER=gemini exige GEMINI_API_KEY configurada."
            )
        return GeminiAIProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )

    raise ConfigurationError(
        f"AI_PROVIDER inválido: '{settings.ai_provider}'. Use 'ollama' ou 'gemini'."
    )