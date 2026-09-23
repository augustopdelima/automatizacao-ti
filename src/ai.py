import os

from google import genai
from pydantic import BaseModel
from typing import Literal


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

    equipe: Literal[
        "SUPORTE",
        "INFRAESTRUTURA",
        "DESENVOLVIMENTO",
    ]


client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


def analisar_solicitacao(mensagem: str) -> AnaliseSolicitacao:
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
- SUPORTE: problemas gerais de usuário.
- INFRAESTRUTURA: rede, servidores, indisponibilidade geral ou infraestrutura.
- DESENVOLVIMENTO: erros ou problemas relacionados a sistemas e aplicações.

Crie também um resumo curto e objetivo.

Solicitação do usuário:
{mensagem}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": AnaliseSolicitacao,
        },
    )

    return AnaliseSolicitacao.model_validate_json(
        response.text
    )
