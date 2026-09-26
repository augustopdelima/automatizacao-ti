"""Configurações da aplicação, centralizadas em um único lugar.

Toda leitura de variáveis de ambiente acontece aqui. Os demais módulos
recebem um objeto Settings montado pela composição (main.py ou testes).
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Configuração inválida ou incompleta."""


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    ai_provider: str
    ollama_base_url: str
    ollama_model: str
    gemini_api_key: str
    gemini_model: str
    database_path: Path
    telegram_connect_timeout: int = 15
    telegram_read_timeout: int = 30
    equipe_suporte_chat_id: str | None = None
    equipe_infraestrutura_chat_id: str | None = None
    equipe_desenvolvimento_chat_id: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        """Monta as configurações a partir do ambiente.

        Sem argumentos, carrega o arquivo .env (se existir) e lê os.environ.
        Em testes, passe um mapping explícito para não depender do ambiente.
        """
        if env is None:
            load_dotenv()
            ambiente = os.environ
        else:
            ambiente = env

        provider = ambiente.get("AI_PROVIDER", "gemini").strip().lower()
        if provider not in {"ollama", "gemini"}:
            raise ConfigurationError(
                f"AI_PROVIDER inválido: '{provider}'. Use 'ollama' ou 'gemini'."
            )

        return cls(
            telegram_bot_token=ambiente.get("TELEGRAM_BOT_TOKEN", ""),
            ai_provider=provider,
            ollama_base_url=ambiente.get(
                "OLLAMA_BASE_URL", "http://localhost:11434"
            ),
            ollama_model=ambiente.get("OLLAMA_MODEL", ""),
            gemini_api_key=ambiente.get("GEMINI_API_KEY", ""),
            gemini_model=ambiente.get("GEMINI_MODEL", "gemini-3.8-flash"),
            database_path=Path(
                ambiente.get("DATABASE_PATH", "/app/data/automation.db")
            ),
            telegram_connect_timeout=int(
                ambiente.get("TELEGRAM_CONNECT_TIMEOUT", "15")
            ),
            telegram_read_timeout=int(ambiente.get("TELEGRAM_READ_TIMEOUT", "30")),
            equipe_suporte_chat_id=ambiente.get("EQUIPE_SUPORTE_CHAT_ID"),
            equipe_infraestrutura_chat_id=ambiente.get(
                "EQUIPE_INFRAESTRUTURA_CHAT_ID"
            ),
            equipe_desenvolvimento_chat_id=ambiente.get(
                "EQUIPE_DESENVOLVIMENTO_CHAT_ID"
            ),
        )