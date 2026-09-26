"""Testes da composição: seleção do provider e criação do repositório."""

from pathlib import Path

import pytest

from src.adapters.outbound.ai.gemini import GeminiAIProvider
from src.adapters.outbound.ai.ollama import OllamaAIProvider
from src.adapters.outbound.persistence.sqlite.repository import (
    SQLiteAutomationRepository,
)
from src.config.composition import criar_provider_ia, criar_repositorio
from src.config.settings import ConfigurationError, Settings


def test_seleciona_ollama():
    settings = Settings.from_env(
        {
            "AI_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://ollama:11434",
            "OLLAMA_MODEL": "qwen3.5:4b",
        }
    )
    provider = criar_provider_ia(settings)
    assert isinstance(provider, OllamaAIProvider)
    assert provider.name == "ollama"


def test_seleciona_gemini():
    settings = Settings.from_env(
        {
            "AI_PROVIDER": "gemini",
            "GEMINI_API_KEY": "chave",
            "GEMINI_MODEL": "gemini-3.8-flash",
        }
    )
    provider = criar_provider_ia(settings)
    assert isinstance(provider, GeminiAIProvider)
    assert provider.name == "gemini"


def test_ollama_sem_modelo_falha():
    settings = Settings.from_env({"AI_PROVIDER": "ollama", "OLLAMA_BASE_URL": "http://x"})
    with pytest.raises(ConfigurationError):
        criar_provider_ia(settings)


def test_gemini_sem_chave_falha():
    settings = Settings.from_env({"AI_PROVIDER": "gemini"})
    with pytest.raises(ConfigurationError):
        criar_provider_ia(settings)


def test_provider_invalido_falha():
    # Settings montado manualmente (sem a validação do from_env, que já
    # rejeitaria antes): o criar_provider_ia também se defende de um
    # ai_provider inválido.
    settings = Settings(
        telegram_bot_token="",
        ai_provider="claude",
        ollama_base_url="http://localhost:11434",
        ollama_model="",
        gemini_api_key="",
        gemini_model="gemini-3.8-flash",
        database_path=Path("/tmp/x.db"),
    )
    with pytest.raises(ConfigurationError):
        criar_provider_ia(settings)


def test_cria_repositorio_sqlite(tmp_path):
    settings = Settings.from_env({"DATABASE_PATH": str(tmp_path / "teste.db")})
    repositorio = criar_repositorio(settings)
    assert isinstance(repositorio, SQLiteAutomationRepository)
    assert repositorio._database_path == tmp_path / "teste.db"