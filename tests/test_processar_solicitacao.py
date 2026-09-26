"""Testes do caso de uso ProcessarSolicitacaoUseCase.

Usam FakeAIProvider e FakeRepository (em memória) para não depender de
serviços externos (Ollama, Gemini, Telegram ou banco real).
"""

import pytest

from fakes import FakeAIProvider, FakeRepository
from src.application.ports.ai_provider import AIUnavailableError
from src.application.ports.repository import PersistenceError
from src.application.use_cases.processar_solicitacao import (
    ProcessarSolicitacaoUseCase,
)
from src.domain.entities import Equipe


JSON_VALIDO = (
    '{"categoria": "REDE", "prioridade": "CRITICA", '
    '"resumo": "Internet caiu", "equipe": "INFRAESTRUTURA"}'
)


def test_classifica_e_persiste(repo):
    provider = FakeAIProvider(resposta=JSON_VALIDO)
    caso_de_uso = ProcessarSolicitacaoUseCase(provider, repo)

    chamado = caso_de_uso.executar(
        mensagem="A internet do laboratório caiu",
        usuario_id=123,
        usuario_username="@bruno",
    )

    assert chamado.id == 1
    assert chamado.classificado
    assert chamado.categoria == "REDE"
    assert chamado.prioridade == "CRITICA"
    assert chamado.resumo == "Internet caiu"
    assert chamado.equipe_sugerida == "INFRAESTRUTURA"
    assert chamado.equipe is not None
    assert chamado.equipe.nome == "INFRAESTRUTURA"
    # Persistido no repositório.
    assert repo.buscar_chamado(1) is chamado
    # O prompt enviado ao provedor lista as equipes ativas do banco.
    assert "INFRAESTRUTURA" in provider.ultimo_prompt


def test_equipe_inexistente_no_banco(repo):
    provider = FakeAIProvider(
        resposta=(
            '{"categoria": "SISTEMA", "prioridade": "ALTA", '
            '"resumo": "bug", "equipe": "RH"}'
        )
    )
    caso_de_uso = ProcessarSolicitacaoUseCase(provider, repo)

    chamado = caso_de_uso.executar("erro no sistema", 1, None)

    assert chamado.classificado
    assert chamado.equipe is None
    assert chamado.equipe_sugerida == "RH"
    assert "RH" in chamado.motivo_sem_encaminhamento()


def test_equipe_ativa_sem_grupo_nao_recebe(repo):
    # SUPORTE sem telegram_chat_id configurado.
    repo.equipes = [
        Equipe(id=1, nome="SUPORTE", telegram_chat_id=None),
        Equipe(id=2, nome="INFRAESTRUTURA", telegram_chat_id="-100infra"),
        Equipe(id=3, nome="DESENVOLVIMENTO", telegram_chat_id="-100dev"),
    ]
    provider = FakeAIProvider(
        resposta=(
            '{"categoria": "ACESSO", "prioridade": "MEDIA", '
            '"resumo": "login", "equipe": "SUPORTE"}'
        )
    )
    caso_de_uso = ProcessarSolicitacaoUseCase(provider, repo)

    chamado = caso_de_uso.executar("não consigo logar", 2, None)

    assert chamado.classificado
    assert chamado.equipe is not None
    assert not chamado.equipe.pode_receber()
    assert "telegram_chat_id" in chamado.motivo_sem_encaminhamento()


def test_fallback_suporte_quando_ia_indisponivel(repo):
    provider = FakeAIProvider(erro=AIUnavailableError("ollama fora do ar"))
    caso_de_uso = ProcessarSolicitacaoUseCase(provider, repo)

    chamado = caso_de_uso.executar("não consigo logar", 456, None)

    assert chamado.id == 1
    assert not chamado.classificado
    assert chamado.categoria is None
    assert chamado.prioridade is None
    assert chamado.equipe is not None
    assert chamado.equipe.nome == "SUPORTE"
    assert repo.buscar_chamado(1) is chamado


def test_fallback_suporte_quando_resposta_invalida(repo):
    provider = FakeAIProvider(resposta="isto não é um json válido")
    caso_de_uso = ProcessarSolicitacaoUseCase(provider, repo)

    chamado = caso_de_uso.executar("problema no sistema", 789, "@ana")

    assert not chamado.classificado
    assert chamado.equipe is not None
    assert chamado.equipe.nome == "SUPORTE"


def test_fallback_suporte_quando_equipe_padrao_ausente(repo):
    # Banco sem SUPORTE: o chamado falho ainda é salvo, apenas sem equipe.
    repo.equipes = [
        Equipe(id=2, nome="INFRAESTRUTURA", telegram_chat_id="-100infra"),
    ]
    provider = FakeAIProvider(erro=AIUnavailableError("gemini indisponível"))
    caso_de_uso = ProcessarSolicitacaoUseCase(provider, repo)

    chamado = caso_de_uso.executar("sem luz no galpão", 10, None)

    assert chamado.id == 1
    assert not chamado.classificado
    assert chamado.equipe is None
    assert "SUPORTE" in chamado.motivo_sem_encaminhamento()


def test_erro_de_persistencia_propaga(repo):
    class RepoQueFalha(FakeRepository):
        def salvar_chamado(self, chamado):
            raise PersistenceError("banco indisponível")

    provider = FakeAIProvider(resposta=JSON_VALIDO)
    caso_de_uso = ProcessarSolicitacaoUseCase(provider, RepoQueFalha())

    with pytest.raises(PersistenceError):
        caso_de_uso.executar("mensagem", 1, None)