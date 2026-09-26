"""Value objects do domínio: o resultado da classificação feita pela IA."""

import unicodedata
from typing import Literal

from pydantic import BaseModel, model_validator

CATEGORIAS = ("SISTEMA", "HARDWARE", "REDE", "ACESSO")
PRIORIDADES = ("BAIXA", "MEDIA", "ALTA", "CRITICA")

# Palavras-chave usadas para mapear respostas livres da IA para os literais
# esperados (a IA nem sempre respeita acento, caixa ou vocabulário exato).
SINONIMOS_CATEGORIA = {
    "SISTEMA": ("SISTEMA", "APLICACAO", "APLICATIVO", "SOFTWARE", "PROGRAMA"),
    "HARDWARE": ("HARDWARE", "EQUIPAMENTO", "PERIFERIC", "FISIC", "MAQUINA"),
    "REDE": ("REDE", "INTERNET", "WIFI", "WI-FI", "CONEXAO", "WIRELESS"),
    "ACESSO": ("ACESSO", "LOGIN", "SENHA", "PERMISSAO", "CREDENCIAL"),
}

SINONIMOS_PRIORIDADE = {
    "BAIXA": ("BAIXA", "BAIXO", "LOW"),
    "MEDIA": ("MEDIA", "MEDIO", "MODERAD"),
    "ALTA": ("ALTA", "ALTO", "HIGH", "URGENT"),
    "CRITICA": ("CRITICA", "CRITICO", "EMERGENC", "FORA DO AR", "INDISPONIVEL"),
}


def _sem_acentos(texto: str) -> str:
    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caractere) != "Mn"
    )


def normalizar_texto(valor: str) -> str:
    """Maiúsculas, sem acentos e sem espaços nas bordas."""
    return _sem_acentos(str(valor)).strip().upper()


def normalizar_equipe(valor: str) -> str:
    """Normaliza o nome de equipe vindo da IA (caixa e acentos)."""
    return normalizar_texto(valor)


def _mapear_para(
    valor: str,
    validos: tuple[str, ...],
    sinonimos: dict[str, tuple[str, ...]],
) -> str:
    texto = normalizar_texto(valor)
    if texto in validos:
        return texto
    for chave, palavras in sinonimos.items():
        if any(palavra in texto for palavra in palavras):
            return chave
    # Sem correspondência: devolve como está e a validação decide (fallback).
    return texto


class AnaliseSolicitacao(BaseModel):
    """Estrutura esperada na resposta da IA ao classificar uma solicitação.

    É o contrato entre o caso de uso e qualquer provedor de IA: quem responde
    deve produzir um JSON com estes campos e valores válidos. A normalização
    (chaves em qualquer caixa, acentos e nomes descritivos) tolera modelos que
    não seguem o vocabulário exato — comum em LLMs locais.
    """

    categoria: Literal["SISTEMA", "HARDWARE", "REDE", "ACESSO"]

    prioridade: Literal["BAIXA", "MEDIA", "ALTA", "CRITICA"]

    resumo: str

    # O nome da equipe é validado pelo Python contra as equipes cadastradas
    # no banco de dados (fonte da verdade para o roteamento).
    equipe: str

    @model_validator(mode="before")
    @classmethod
    def _aceitar_respostas_livres(cls, dados):
        """Normaliza a resposta da IA antes da validação.

        Tolerâncias:
        - chaves em qualquer caixa (ex.: "Resumo" → "resumo");
        - acentos e caixa livre nos valores (ex.: "Média" → "MEDIA");
        - valores descritivos (ex.: "Hardware / Falha de Equipamento" →
          "HARDWARE").
        """
        if not isinstance(dados, dict):
            return dados

        dados = {str(chave).strip().lower(): valor for chave, valor in dados.items()}

        if "categoria" in dados:
            dados["categoria"] = _mapear_para(
                dados["categoria"], CATEGORIAS, SINONIMOS_CATEGORIA
            )
        if "prioridade" in dados:
            dados["prioridade"] = _mapear_para(
                dados["prioridade"], PRIORIDADES, SINONIMOS_PRIORIDADE
            )
        if "resumo" in dados and dados["resumo"] is not None:
            dados["resumo"] = str(dados["resumo"]).strip()
        if "equipe" in dados:
            dados["equipe"] = normalizar_equipe(dados["equipe"])

        return dados