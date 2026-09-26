"""Testes do caso de uso ConsultarChamadoUseCase."""

from src.application.use_cases.consultar_chamado import ConsultarChamadoUseCase
from src.domain.entities import Chamado


def test_consulta_retorna_chamado_salvo(repo):
    equipe = repo.buscar_equipe_por_nome("SUPORTE")
    chamado = Chamado(
        id=None,
        mensagem="não consigo logar",
        usuario_id=1,
        usuario_username="@ana",
        categoria="ACESSO",
        prioridade="MEDIA",
        resumo="erro de login",
        equipe_sugerida="SUPORTE",
        equipe=equipe,
    )
    protocolo = repo.salvar_chamado(chamado)
    # O id é atribuído após salvar (mesmo contrato do caso de uso Processar).
    chamado.id = protocolo

    caso_de_uso = ConsultarChamadoUseCase(repo)
    chamado = caso_de_uso.executar(protocolo)

    assert chamado is not None
    assert chamado.id == protocolo
    assert chamado.mensagem == "não consigo logar"
    assert chamado.categoria == "ACESSO"
    assert chamado.equipe is not None
    assert chamado.equipe.nome == "SUPORTE"


def test_consulta_protocolo_inexistente(repo):
    caso_de_uso = ConsultarChamadoUseCase(repo)
    assert caso_de_uso.executar(999) is None