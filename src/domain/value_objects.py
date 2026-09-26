"""Value objects do domínio: o resultado da classificação feita pela IA."""

from typing import Literal

from pydantic import BaseModel


class AnaliseSolicitacao(BaseModel):
    """Estrutura esperada na resposta da IA ao classificar uma solicitação.

    É o contrato entre o caso de uso e qualquer provedor de IA: quem responde
    deve produzir um JSON com estes campos e valores válidos.
    """

    categoria: Literal["SISTEMA", "HARDWARE", "REDE", "ACESSO"]

    prioridade: Literal["BAIXA", "MEDIA", "ALTA", "CRITICA"]

    resumo: str

    # O nome da equipe é validado pelo Python contra as equipes cadastradas
    # no banco de dados (fonte da verdade para o roteamento).
    equipe: str