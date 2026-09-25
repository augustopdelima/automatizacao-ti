"""Textos das mensagens enviadas pelo bot no Telegram."""

from .service import Chamado


def confirmacao(chamado: Chamado, nome_equipe: str, encaminhado: bool) -> str:
    texto = (
        "✅ Solicitação registrada!\n\n"
        f"📋 Protocolo: #{chamado.id}\n"
        f"🏷️ Categoria: {chamado.analise.categoria}\n"
        f"🚨 Prioridade: {chamado.analise.prioridade}\n"
        f"👥 Equipe responsável: {nome_equipe}\n\n"
        f"📝 Resumo:\n{chamado.analise.resumo}\n"
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
        f"🏷️ Categoria: {chamado.analise.categoria}\n"
        f"🚨 Prioridade: {chamado.analise.prioridade}\n"
        f"👥 Equipe: {nome_equipe}\n\n"
        f"📝 Solicitação:\n{chamado.mensagem}\n\n"
        f"📝 Resumo:\n{chamado.analise.resumo}\n\n"
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


def consulta(solicitacao) -> str:
    linhas = [
        f"Solicitação #{solicitacao['id']}",
        "",
        f"Mensagem: {solicitacao['mensagem']}",
        f"Status: {solicitacao['status']}",
        f"Criada em: {solicitacao['criado_em']}",
    ]

    if solicitacao["categoria"]:
        linhas.append(f"Categoria: {solicitacao['categoria']}")
    if solicitacao["prioridade"]:
        linhas.append(f"Prioridade: {solicitacao['prioridade']}")
    if solicitacao["resumo"]:
        linhas.append(f"Resumo: {solicitacao['resumo']}")
    if solicitacao["equipe_nome"]:
        linhas.append(f"Equipe: {solicitacao['equipe_nome']}")

    return "\n".join(linhas)