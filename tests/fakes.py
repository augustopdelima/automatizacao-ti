"""Fakes (implementações falsas das portas) para os testes.

Permitem testar casos de uso sem iniciar Ollama, chamar o Gemini, acessar o
Telegram ou tocar em um banco real.
"""

from src.domain.entities import Chamado, Equipe


class FakeAIProvider:
    """Provedor de IA fake: guarda o último prompt e responde com texto fixo."""

    name = "fake"

    def __init__(self, resposta: str | None = None, erro: Exception | None = None):
        self.resposta = resposta
        self.erro = erro
        self.ultimo_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.ultimo_prompt = prompt
        if self.erro is not None:
            raise self.erro
        if self.resposta is None:
            raise AssertionError("FakeAIProvider sem resposta configurada.")
        return self.resposta


class FakeRepository:
    """Repositório em memória que implementa a porta AutomationRepository."""

    def __init__(self, equipes: list[Equipe] | None = None):
        self.equipes = equipes if equipes is not None else [
            Equipe(id=1, nome="SUPORTE", telegram_chat_id="-100suporte"),
            Equipe(id=2, nome="INFRAESTRUTURA", telegram_chat_id="-100infra"),
            Equipe(id=3, nome="DESENVOLVIMENTO", telegram_chat_id="-100dev"),
        ]
        self.chamados: dict[int, Chamado] = {}
        self._proximo_id = 1

    def criar_tabelas(self) -> None:
        return None

    def salvar_chamado(self, chamado: Chamado) -> int:
        protocolo = self._proximo_id
        self._proximo_id += 1
        self.chamados[protocolo] = chamado
        return protocolo

    def buscar_chamado(self, protocolo: int) -> Chamado | None:
        return self.chamados.get(protocolo)

    def listar_equipes_ativas(self) -> list[str]:
        return [e.nome for e in self.equipes if e.ativa]

    def buscar_equipe_por_nome(self, nome: str) -> Equipe | None:
        for equipe in self.equipes:
            if equipe.nome.lower() == nome.lower():
                return equipe
        return None

    def atualizar_telegram_chat_id(self, nome: str, telegram_chat_id: str) -> bool:
        for equipe in self.equipes:
            if equipe.nome.lower() == nome.lower():
                equipe.telegram_chat_id = telegram_chat_id
                return True
        return False