"""Testes da leitura de configuração (Settings.from_env)."""

from pathlib import Path

import pytest

from src.config.settings import ConfigurationError, Settings


def test_padrao_e_gemini():
    settings = Settings.from_env({})
    assert settings.ai_provider == "gemini"
    assert settings.gemini_model == "gemini-3.8-flash"
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_model == ""
    assert settings.gemini_api_key == ""
    assert settings.database_path == Path("/app/data/automation.db")


def test_provider_ollama():
    settings = Settings.from_env(
        {
            "AI_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://host.containers.internal:11434",
            "OLLAMA_MODEL": "gemma4:12b",
        }
    )
    assert settings.ai_provider == "ollama"
    assert settings.ollama_base_url == "http://host.containers.internal:11434"
    assert settings.ollama_model == "gemma4:12b"


def test_provider_ignora_maiusculas_e_espacos():
    settings = Settings.from_env({"AI_PROVIDER": "  OLLAMA "})
    assert settings.ai_provider == "ollama"


def test_provider_invalido():
    with pytest.raises(ConfigurationError):
        Settings.from_env({"AI_PROVIDER": "azure"})


def test_database_path_personalizado():
    settings = Settings.from_env({"DATABASE_PATH": "/tmp/meu.db"})
    assert settings.database_path == Path("/tmp/meu.db")


def test_configuracao_completa_gemini():
    settings = Settings.from_env(
        {
            "AI_PROVIDER": "gemini",
            "GEMINI_API_KEY": "chave",
            "GEMINI_MODEL": "gemini-2.0-flash",
            "TELEGRAM_BOT_TOKEN": "token",
            "EQUIPE_SUPORTE_CHAT_ID": "-1001",
            "EQUIPE_INFRAESTRUTURA_CHAT_ID": "-1002",
            "EQUIPE_DESENVOLVIMENTO_CHAT_ID": "-1003",
        }
    )
    assert settings.ai_provider == "gemini"
    assert settings.gemini_api_key == "chave"
    assert settings.gemini_model == "gemini-2.0-flash"
    assert settings.telegram_bot_token == "token"
    assert settings.equipe_suporte_chat_id == "-1001"
    assert settings.equipe_infraestrutura_chat_id == "-1002"
    assert settings.equipe_desenvolvimento_chat_id == "-1003"


def test_timeouts_padrao():
    settings = Settings.from_env({})
    assert settings.telegram_connect_timeout == 15
    assert settings.telegram_read_timeout == 30