"""Caso de uso: consultar um chamado pelo protocolo."""

from ...domain.entities import Chamado
from ..ports.repository import AutomationRepository


class ConsultarChamadoUseCase:
    """Retorna o chamado pelo protocolo, ou None se não existir.

    É propositalmente fino: apenas expõe uma consulta simples do repositório
    sem acoplar o adapter de entrada do Telegram à persistência.
    """

    def __init__(self, repository: AutomationRepository):
        self._repository = repository

    def executar(self, protocolo: int) -> Chamado | None:
        return self._repository.buscar_chamado(protocolo)