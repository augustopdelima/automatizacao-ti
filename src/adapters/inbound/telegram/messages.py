"""Textos das mensagens enviadas pelo bot no Telegram (apresentação).

Este módulo pertence ao adapter de entrada: formata os dados de domínio
(Chamado/Equipe) em texto. Nenhuma regra de negócio vive aqui.
"""

from ....domain.entities import Chamado


def processing() -> str:
    """Aviso imediato de que a solicitação foi recebida (antes da análise).

    Enviada pelo adapter assim que a mensagem é qualificada como solicitação
    de suporte, antes do processamento demorado (chamada de IA/persistência).
    """
    return (
        "🛠️ Recebi sua solicitação de suporte. "
        "Vou analisar o problema e já retorno com uma resposta."
    )


def confirmacao(chamado: Chamado, nome_equipe: str, encaminhado: bool) -> str:
    texto = (
        "✅ Solicitação registrada!\n\n"
        f"📋 Protocolo: #{chamado.id}\n"
        f"🏷️ Categoria: {chamado.categoria}\n"
        f"🚨 Prioridade: {chamado.prioridade}\n"
        f"👥 Equipe responsável: {nome_equipe}\n\n"
        f"📝 Resumo:\n{chamado.resumo}\n"
    )

    if encaminhado:
        return texto + "\nSua solicitação foi encaminhada para a equipe responsável."

    return texto + (
        "\n⚠️ Não foi possível encaminhar para a equipe agora. "
        "O chamado está registrado e será tratado pela equipe de suporte."
    )


def novo_chamado(chamado: Chamado, nome_solicitante: str, nome_equipe: str) -> str:
    return (
        "🔔 NOVO CHAMADO\n\n"
        f"📋 Protocolo: #{chamado.id}\n\n"
        f"👤 Solicitante: {nome_solicitante}\n"
        f"🏷️ Categoria: {chamado.categoria}\n"
        f"🚨 Prioridade: {chamado.prioridade}\n"
        f"👥 Equipe: {nome_equipe}\n\n"
        f"📝 Solicitação:\n{chamado.mensagem}\n\n"
        f"📝 Resumo:\n{chamado.resumo}\n\n"
        "⏱️ Status: ABERTA"
    )


def novo_chamado_sem_analise(
    chamado: Chamado,
    nome_solicitante: str,
    nome_equipe: str,
) -> str:
    return (
        "🔔 NOVO CHAMADO (sem classificação automática)\n\n"
        f"📋 Protocolo: #{chamado.id}\n\n"
        f"👤 Solicitante: {nome_solicitante}\n"
        f"👥 Equipe: {nome_equipe}\n\n"
        f"📝 Solicitação:\n{chamado.mensagem}\n\n"
        "⚠️ A classificação automática falhou; aguardando triagem manual.\n\n"
        "⏱️ Status: ABERTA"
    )


def sem_classificacao(chamado_id: int) -> str:
    return (
        "✅ Solicitação registrada!\n\n"
        f"📋 Protocolo: #{chamado_id}\n\n"
        "Não foi possível classificar a solicitação automaticamente. "
        "Ela será analisada manualmente pela equipe de suporte."
    )


def sem_classificacao_suporte(
    chamado: Chamado,
    nome_equipe: str,
    encaminhado: bool,
) -> str:
    texto = (
        "✅ Solicitação registrada!\n\n"
        f"📋 Protocolo: #{chamado.id}\n"
        "🤖 A classificação automática falhou. O chamado foi atribuído "
        f"por padrão à equipe {nome_equipe}.\n"
    )

    if encaminhado:
        return texto + "\nSua solicitação foi encaminhada para a equipe responsável."

    return texto + (
        "\n⚠️ Não foi possível encaminhar para a equipe agora. "
        "O chamado está registrado e será tratado pela equipe de suporte."
    )


def consulta(chamado: Chamado) -> str:
    linhas = [
        f"Solicitação #{chamado.id}",
        "",
        f"Mensagem: {chamado.mensagem}",
        f"Status: {chamado.status}",
        f"Criada em: {chamado.criado_em or '—'}",
    ]

    if chamado.categoria:
        linhas.append(f"Categoria: {chamado.categoria}")
    if chamado.prioridade:
        linhas.append(f"Prioridade: {chamado.prioridade}")
    if chamado.resumo:
        linhas.append(f"Resumo: {chamado.resumo}")
    if chamado.equipe is not None:
        linhas.append(f"Equipe: {chamado.equipe.nome}")

    return "\n".join(linhas)