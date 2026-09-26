"""Caso de uso: classificar uma solicitação e registrá-la como chamado.

Depende apenas das portas AIProvider e AutomationRepository. A decisão de
qual provedor (Ollama/Gemini) é da composição — este módulo não conhece as
tecnologias.
"""

import logging

from pydantic import ValidationError

from ...domain.entities import Chamado
from ...domain.value_objects import AnaliseSolicitacao, normalizar_equipe
from ..ports.ai_provider import AIProvider, AIProviderError
from ..ports.repository import AutomationRepository

logger = logging.getLogger(__name__)

# Descrições usadas apenas para orientar a classificação da IA. A lista de
# equipes válidas vem do banco de dados em tempo de execução.
DESCRICOES_EQUIPES = {
    "SUPORTE": "problemas gerais de usuário",
    "INFRAESTRUTURA": "rede, servidores, indisponibilidade geral ou infraestrutura",
    "DESENVOLVIMENTO": "erros ou problemas relacionados a sistemas e aplicações",
}

# Equipe usada quando a classificação falha (fallback).
EQUIPE_PADRAO = "SUPORTE"


def _resolver_equipe(sugerida: str, equipes: list[str]) -> str:
    """Casa o nome de equipe sugerido pela IA com uma equipe cadastrada.

    A IA pode escrever o nome de forma livre (ex.: 'Suporte Técnico de
    Hardware' → SUPORTE). Primeiro tenta correspondência exata; depois, o
    nome da equipe que aparecer primeiro dentro da sugestão. Sem
    correspondência, devolve a sugestão original (o fluxo existente trata
    equipe desconhecida como sem encaminhamento).
    """
    alvo = normalizar_equipe(sugerida)

    candidatas: list[tuple[int, str]] = []
    for nome in equipes:
        nome_normalizado = normalizar_equipe(nome)
        if nome_normalizado == alvo:
            return nome
        posicao = alvo.find(nome_normalizado)
        if posicao >= 0:
            candidatas.append((posicao, nome))

    if candidatas:
        # Menor posição; desempate pelo nome de equipe mais curto.
        return min(
            candidatas,
            key=lambda item: (item[0], len(normalizar_equipe(item[1]))),
        )[1]

    return sugerida


def _montar_bloco_equipes(equipes: list[str]) -> str:
    return "\n".join(
        f"- {nome}: {DESCRICOES_EQUIPES.get(nome, 'problemas relacionados à equipe')}."
        for nome in equipes
    )


def _montar_prompt(mensagem: str, equipes: list[str]) -> str:
    return f"""
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

{_montar_bloco_equipes(equipes)}

Crie também um resumo curto e objetivo.

Responda APENAS com um JSON válido, sem texto adicional, com exatamente estas
chaves em minúsculas: categoria, prioridade, resumo, equipe.
Valores exatos:
- categoria: SISTEMA, HARDWARE, REDE ou ACESSO.
- prioridade: BAIXA, MEDIA, ALTA ou CRITICA.
- equipe: apenas uma das equipes listadas acima, pelo nome exato.

Solicitação do usuário:
{mensagem}
"""


class ProcessarSolicitacaoUseCase:
    """Recebe uma mensagem e produz um Chamado classificado e persistido.

    Se a classificação falhar (provedor indisponível ou resposta inválida), o
    chamado é salvo e atribuído por padrão à equipe SUPORTE.
    """

    def __init__(self, provider: AIProvider, repository: AutomationRepository):
        self._provider = provider
        self._repository = repository

    def executar(
        self,
        mensagem: str,
        usuario_id: int,
        usuario_username: str | None,
    ) -> Chamado:
        logger.info("Processando solicitação do usuário %s", usuario_id)

        equipes = self._repository.listar_equipes_ativas()
        analise = self._classificar(mensagem, equipes)

        if analise is not None:
            nome_equipe = _resolver_equipe(analise.equipe, equipes)
            equipe = self._repository.buscar_equipe_por_nome(nome_equipe)
        else:
            # Classificação falhou: atribui o chamado à equipe SUPORTE por
            # padrão, quando ela existir no banco (criada no primeiro start).
            equipe = self._repository.buscar_equipe_por_nome(EQUIPE_PADRAO)

        chamado = Chamado(
            id=None,
            mensagem=mensagem,
            usuario_id=usuario_id,
            usuario_username=usuario_username,
            categoria=analise.categoria if analise else None,
            prioridade=analise.prioridade if analise else None,
            resumo=analise.resumo if analise else None,
            equipe_sugerida=analise.equipe if analise else None,
            equipe=equipe,
        )
        chamado.id = self._repository.salvar_chamado(chamado)

        if analise is not None and (equipe is None or not equipe.pode_receber()):
            logger.warning(
                "Chamado #%s salvo sem encaminhamento: %s",
                chamado.id,
                chamado.motivo_sem_encaminhamento(),
            )

        return chamado

    def _classificar(
        self,
        mensagem: str,
        equipes: list[str],
    ) -> AnaliseSolicitacao | None:
        try:
            logger.info("Classificando com provedor de IA '%s'", self._provider.name)
            resposta = self._provider.generate(_montar_prompt(mensagem, equipes))
            return AnaliseSolicitacao.model_validate_json(resposta)
        except (AIProviderError, ValidationError) as error:
            logger.error("Falha ao classificar a solicitação: %s", error)
            return None