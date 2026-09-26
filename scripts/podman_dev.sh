#!/usr/bin/env bash
#
# Builda a imagem de produção e gerencia o container do bot no ambiente de dev.
#
# Uso:
#   bash scripts/podman_dev.sh               # build + sobe/substitui o container
#   bash scripts/podman_dev.sh --build-only  # apenas constrói a imagem
#   bash scripts/podman_dev.sh --logs        # acompanha os logs do container
#   bash scripts/podman_dev.sh --remove      # para e remove o container
#   REDE=botnet bash scripts/podman_dev.sh   # coloca o bot na rede "botnet"
#                                            # (Opção B do README: Ollama em container)
#   REDE=host bash scripts/podman_dev.sh     # usa a rede do host (Ollama nativo na
#                                            # máquina + http://localhost:11434)
#
# Variáveis de ambiente:
#   NAME=...            nome do container (padrão: automatizacao-ti)
#   REDE=botnet         rede Podman do container (opcional; Opção B do README)
#   REDE=host           rede do host — o localhost do bot é o da máquina
#                       (use junto com OLLAMA_BASE_URL=http://localhost:11434)
#   BIND_DADOS=/caminho/para/data   usa bind mount no lugar do volume nomeado
#   SELINUX=1           acrescenta ":Z" aos bind mounts (Fedora e similares)

set -euo pipefail

NAME="${NAME:-automatizacao-ti}"
IMAGEM="${IMAGEM:-automatizacao-ti}"
VOLUME_DADOS="${VOLUME_DADOS:-automatizacao_ti_data}"
ARQUIVO_ENV=".env"

ACAO="run"   # run | build | logs | remove

usage() {
    cat <<'EOF'
Builda a imagem de produção e gerencia o container do bot no ambiente de dev.

Uso:
  bash scripts/podman_dev.sh               # build + sobe/substitui o container
  bash scripts/podman_dev.sh --build-only  # apenas constrói a imagem
  bash scripts/podman_dev.sh --logs        # acompanha os logs do container
  bash scripts/podman_dev.sh --remove      # para e remove o container
  REDE=botnet bash scripts/podman_dev.sh   # coloca o bot na rede "botnet"
                                           # (Opção B do README: Ollama em container)
  REDE=host bash scripts/podman_dev.sh     # usa a rede do host (Ollama nativo na
                                           # máquina + http://localhost:11434)

Variáveis de ambiente:
  NAME=...            nome do container (padrão: automatizacao-ti)
  REDE=botnet         rede Podman do container (opcional; Opção B do README)
  REDE=host           rede do host — o localhost do bot é o da máquina
                      (use junto com OLLAMA_BASE_URL=http://localhost:11434)
  BIND_DADOS=/caminho/para/data   usa bind mount no lugar do volume nomeado
  SELINUX=1           acrescenta ":Z" aos bind mounts (Fedora e similares)
EOF
}

for arg in "$@"; do
    case "$arg" in
        --build-only) ACAO="build" ;;
        --logs)       ACAO="logs" ;;
        --remove)     ACAO="remove" ;;
        -h|--help)    usage; exit 0 ;;
        *)
            echo "Argumento desconhecido: $arg" >&2
            usage
            exit 1
            ;;
    esac
done

if ! command -v podman >/dev/null 2>&1; then
    echo "Erro: 'podman' não encontrado no PATH." >&2
    exit 1
fi

case "$ACAO" in
    build)
        echo ">> Construindo imagem de produção ($IMAGEM)..."
        podman build -t "$IMAGEM" .
        ;;
    logs)
        podman logs -f "$NAME"
        ;;
    remove)
        if podman container exists "$NAME"; then
            echo ">> Removendo container '$NAME'..."
            podman stop "$NAME" || true
            podman rm "$NAME"
        else
            echo "Container '$NAME' não existe."
        fi
        ;;
    run)
        if [[ ! -f "$ARQUIVO_ENV" ]]; then
            echo "Erro: '$ARQUIVO_ENV' não encontrado. Copie de .example.env e preencha." >&2
            exit 1
        fi

        echo ">> Construindo imagem de produção ($IMAGEM)..."
        podman build -t "$IMAGEM" .

        # Substitui o container atual, se existir (idempotente)
        if podman container exists "$NAME"; then
            echo ">> Container '$NAME' já existe; parando e removendo..."
            podman stop "$NAME" || true
            podman rm "$NAME"
        fi

        RUN_ARGS=(run -d --name "$NAME" --env-file "$ARQUIVO_ENV" --restart unless-stopped)

        if [[ -n "${REDE:-}" ]]; then
            RUN_ARGS+=(--network "$REDE")
            echo ">> Usando rede '$REDE'."
        fi

        if [[ -n "${BIND_DADOS:-}" ]]; then
            MOUNT="$BIND_DADOS:/app/data"
            if [[ "${SELINUX:-0}" == "1" ]]; then
                MOUNT="${MOUNT}:Z"
            fi
            RUN_ARGS+=(-v "$MOUNT")
            echo ">> Dados em bind mount '$BIND_DADOS'."
        else
            RUN_ARGS+=(-v "$VOLUME_DADOS:/app/data")
        fi

        echo ">> Subindo container '$NAME'..."
        podman "${RUN_ARGS[@]}" "$IMAGEM"

        echo ">> Pronto. Acompanhe com: podman logs -f $NAME"
        ;;
esac