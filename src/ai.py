import logging
import os
import time

from google import genai
from pydantic import BaseModel
from typing import Literal


# Descrições usadas apenas para orientar a classificação da IA.
# A lista de equipes válidas vem do banco de dados em tempo de execução.
DESCRICOES_EQUIPES = {
    "SUPORTE": "problemas gerais de usuário",
    "INFRAESTRUTURA": "rede, servidores, indisponibilidade geral ou infraestrutura",
    "DESENVOLVIMENTO": "erros ou problemas relacionados a sistemas e aplicações",
}


class AnaliseSolicitacao(BaseModel):
    categoria: Literal[
        "SISTEMA",
        "HARDWARE",
        "REDE",
        "ACESSO",
    ]

    prioridade: Literal[
        "BAIXA",
        "MEDIA",
        "ALTA",
        "CRITICA",
    ]

    resumo: str

    # O nome da equipe é validado pelo Python contra as equipes cadastradas
    # no banco de dados (fonte da verdade para o roteamento).
    equipe: str


client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

logger = logging.getLogger(__name__)

# Modelo do Gemini usado na classificação. Padrão: gemini-3.8-flash.
# Pode ser sobrescrito via GEMINI_MODEL no .env.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

# A API pode responder 503 ("demanda alta") de forma temporária, e a própria
# mensagem de erro recomenda tentar novamente. O retry com backoff evita que
# a classificação seja perdida por causa de um pico momentâneo.
MAX_TENTATIVAS = 3


def _montar_bloco_equipes(equipes: list[str]) -> str:
    return "\n".join(
        f"- {nome}: {DESCRICOES_EQUIPES.get(nome, 'problemas relacionados à equipe')}."
        for nome in equipes
    )


def analisar_solicitacao(
    mensagem: str,
    equipes_disponiveis: list[str],
) -> AnaliseSolicitacao:
    prompt = f"""
Você é um sistema de triagem automática de chamados de suporte de TI.

Analise a solicitação do usuário e classifique o chamado.

Regras:

CATEGORIA:
- SISTEMA: problemas em sistemas ou aplicações.
- HARDWARE: problemas físicos no computador ou periféricos.
- REDE: problemas de internet, Wi-Fi, conexão ou infraestrutura de rede.
- ACESSO: problemas com login, senha, permissões ou acesso a sistemas.

PRIORIDADE:
- BAIXA: dúvida ou problema sem impacto relevante.
- MEDIA: problema que afeta um usuário, mas possui alternativa.
- ALTA: problema que impede uma atividade importante.
- CRITICA: sistema ou serviço essencial indisponível para vários usuários.

EQUIPE:
Escolha a equipe mais adequada para o problema, usando apenas uma das
equipes cadastradas abaixo (não invente nomes de equipes):

{_montar_bloco_equipes(equipes_disponiveis)}

Crie também um resumo curto e objetivo.

Solicitação do usuário:
{mensagem}
"""

    for tentativa in range(MAX_TENTATIVAS):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": AnaliseSolicitacao,
                },
            )

            return AnaliseSolicitacao.model_validate_json(
                response.text
            )
        except Exception as error:
            if tentativa < MAX_TENTATIVAS - 1:
                logger.warning(
                    "Classificação falhou (tentativa %s/%s): %s",
                    tentativa + 1,
                    MAX_TENTATIVAS,
                    error,
                )
                time.sleep(2 * (tentativa + 1))
            else:
                raise
