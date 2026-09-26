"""Testes do repositório SQLite (SQLite em arquivo temporário, sem serviços)."""

import pytest

from src.adapters.outbound.persistence.sqlite.repository import (
    SQLiteAutomationRepository,
)
from src.application.ports.repository import PersistenceError
from src.domain.entities import Chamado


@pytest.fixture
def repositorio(tmp_path) -> SQLiteAutomationRepository:
    repositorio = SQLiteAutomationRepository(tmp_path / "teste.db")
    repositorio.criar_tabelas()
    return repositorio


def test_criar_tabelas_seed_equipes(repositorio):
    equipes = repositorio.listar_equipes_ativas()
    assert set(equipes) == {"SUPORTE", "INFRAESTRUTURA", "DESENVOLVIMENTO"}


def test_salvar_e_buscar_chamado(repositorio):
    equipe = repositorio.buscar_equipe_por_nome("SUPORTE")
    protocolo = repositorio.salvar_chamado(
        Chamado(
            id=None,
            mensagem="não consigo logar",
            usuario_id=42,
            usuario_username="@ana",
            categoria="ACESSO",
            prioridade="MEDIA",
            resumo="erro de login",
            equipe_sugerida="SUPORTE",
            equipe=equipe,
        )
    )

    chamado = repositorio.buscar_chamado(protocolo)

    assert chamado is not None
    assert chamado.id == protocolo
    assert chamado.mensagem == "não consigo logar"
    assert chamado.usuario_id == 42
    assert chamado.usuario_username == "@ana"
    assert chamado.categoria == "ACESSO"
    assert chamado.prioridade == "MEDIA"
    assert chamado.resumo == "erro de login"
    assert chamado.status == "ABERTA"
    assert chamado.criado_em is not None
    assert chamado.equipe is not None
    assert chamado.equipe.nome == "SUPORTE"


def test_salvar_chamado_sem_equipe(repositorio):
    protocolo = repositorio.salvar_chamado(
        Chamado(
            id=None,
            mensagem="sem equipe",
            usuario_id=1,
            usuario_username=None,
            categoria=None,
            prioridade=None,
            resumo=None,
            equipe_sugerida=None,
            equipe=None,
        )
    )

    chamado = repositorio.buscar_chamado(protocolo)

    assert chamado is not None
    assert chamado.equipe is None


def test_buscar_chamado_inexistente(repositorio):
    assert repositorio.buscar_chamado(999) is None


def test_buscar_equipe_por_nome_ignora_maiusculas(repositorio):
    equipe = repositorio.buscar_equipe_por_nome("suporte")
    assert equipe is not None
    assert equipe.nome == "SUPORTE"


def test_atualizar_telegram_chat_id(repositorio):
    assert repositorio.atualizar_telegram_chat_id("SUPORTE", "-100123") is True

    equipe = repositorio.buscar_equipe_por_nome("SUPORTE")
    assert equipe.telegram_chat_id == "-100123"

    assert repositorio.atualizar_telegram_chat_id("INEXISTENTE", "-100") is False


def test_busca_em_banco_inexistente_falha_com_persistence_error(tmp_path):
    repositorio = SQLiteAutomationRepository(tmp_path / "nao-existe.db")

    with pytest.raises(PersistenceError):
        repositorio.listar_equipes_ativas()