"""Testes das regras de negócio do domínio (entities)."""

from src.domain.entities import Chamado, Equipe
from src.domain.value_objects import AnaliseSolicitacao


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


def test_analise_solicitacao_normaliza_chaves_e_valores():
    # Chaves capitalizadas, acentos/caixa livres e valores descritivos da IA
    # são normalizados antes da validação.
    analise = AnaliseSolicitacao.model_validate_json(
        '{"Categoria": "Hardware / Falha de Equipamento", '
        '"Prioridade": "Média", "Resumo": "  não liga  ", '
        '"Equipe": "suporte técnico"}'
    )
    assert analise.categoria == "HARDWARE"
    assert analise.prioridade == "MEDIA"
    assert analise.resumo == "não liga"
    assert analise.equipe == "SUPORTE TECNICO"


def test_analise_solicitacao_aceita_json_no_padrao():
    analise = AnaliseSolicitacao.model_validate_json(
        '{"categoria": "REDE", "prioridade": "CRITICA", '
        '"resumo": "Internet caiu", "equipe": "INFRAESTRUTURA"}'
    )
    assert analise.categoria == "REDE"
    assert analise.prioridade == "CRITICA"
    assert analise.equipe == "INFRAESTRUTURA"