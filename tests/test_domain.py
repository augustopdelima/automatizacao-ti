"""Testes das regras de negócio do domínio (entities)."""

from src.domain.entities import Chamado, Equipe


def test_equipe_ativa_com_grupo_pode_receber():
    equipe = Equipe(id=1, nome="SUPORTE", telegram_chat_id="-100123")
    assert equipe.pode_receber() is True
    assert equipe.motivo_sem_encaminhamento() is None


def test_equipe_inativa_nao_recebe():
    equipe = Equipe(id=1, nome="SUPORTE", telegram_chat_id="-100123", ativa=False)
    assert equipe.pode_receber() is False
    assert equipe.motivo_sem_encaminhamento() == "equipe 'SUPORTE' está inativa"


def test_equipe_sem_grupo_nao_recebe():
    equipe = Equipe(id=1, nome="SUPORTE", telegram_chat_id=None)
    assert equipe.pode_receber() is False
    assert "telegram_chat_id" in equipe.motivo_sem_encaminhamento()


def test_chamado_classificado_quando_tem_categoria():
    chamado = Chamado(
        id=1,
        mensagem="oi",
        usuario_id=1,
        usuario_username=None,
        categoria="REDE",
        prioridade="BAIXA",
        resumo="x",
        equipe_sugerida="SUPORTE",
        equipe=None,
    )
    assert chamado.classificado is True


def test_chamado_nao_classificado_sem_categoria():
    chamado = Chamado(
        id=2,
        mensagem="oi",
        usuario_id=1,
        usuario_username=None,
        categoria=None,
        prioridade=None,
        resumo=None,
        equipe_sugerida=None,
        equipe=None,
    )
    assert chamado.classificado is False


def test_motivo_equipe_nao_cadastrada():
    chamado = Chamado(
        id=3,
        mensagem="oi",
        usuario_id=1,
        usuario_username=None,
        categoria="SISTEMA",
        prioridade="ALTA",
        resumo="x",
        equipe_sugerida="RH",
        equipe=None,
    )
    assert chamado.motivo_sem_encaminhamento() == "equipe 'RH' não cadastrada no banco"