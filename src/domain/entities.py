"""Entidades do domínio: Equipe e Chamado (solicitação de suporte)."""

from dataclasses import dataclass


@dataclass
class Equipe:
    """Equipe responsável por um tipo de chamado."""

    id: int | None
    nome: str
    telegram_chat_id: str | None
    ativa: bool = True

    def pode_receber(self) -> bool:
        """Regra de roteamento: só recebe chamados se ativa e com grupo."""
        return self.ativa and bool(self.telegram_chat_id)

    def motivo_sem_encaminhamento(self) -> str | None:
        """Explica por que a equipe não pode receber o chamado (ou None)."""
        if not self.ativa:
            return f"equipe '{self.nome}' está inativa"
        if not self.telegram_chat_id:
            return f"equipe '{self.nome}' não possui telegram_chat_id configurado"
        return None


@dataclass
class Chamado:
    """Solicitação de suporte já persistida, pronta para ser notificada.

    ``equipe_sugerida`` é o nome da equipe apontado pela IA (mesmo quando ela
    não existe no banco). ``equipe`` é a equipe efetivamente atribuída ao
    chamado (roteamento). Quando a classificação falha, a equipe padrão é a
    SUPORTE.
    """

    id: int | None
    mensagem: str
    usuario_id: int
    usuario_username: str | None
    categoria: str | None
    prioridade: str | None
    resumo: str | None
    equipe_sugerida: str | None
    equipe: Equipe | None
    status: str = "ABERTA"
    criado_em: str | None = None

    @property
    def classificado(self) -> bool:
        """A IA conseguiu classificar este chamado?"""
        return self.categoria is not None

    def motivo_sem_encaminhamento(self) -> str:
        """Motivo para não encaminhar o chamado (usado apenas em logs)."""
        if self.equipe is not None:
            motivo = self.equipe.motivo_sem_encaminhamento()
            return motivo or "motivo desconhecido"

        if self.equipe_sugerida is not None:
            return f"equipe '{self.equipe_sugerida}' não cadastrada no banco"

        return "equipe padrão (SUPORTE) não cadastrada no banco"