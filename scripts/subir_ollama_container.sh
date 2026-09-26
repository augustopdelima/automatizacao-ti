#!/usr/bin/env bash
#
# Sobe o Ollama em um container Podman na rede privada "botnet",
# na mesma rede do bot (ver README: "Ollama em container").
# Nenhuma porta é publicada no host.
#
# Uso:
#   bash scripts/subir_ollama_container.sh                       # modelo padrão gemma4:12b
#   bash scripts/subir_ollama_container.sh gemma4:12b            # modelo específico
#   REUTILIZAR_MODELOS_HOST=1 bash scripts/subir_ollama_container.sh  # reaproveita ~/.ollama do host
#   GPU=1 bash scripts/subir_ollama_container.sh                 # expõe a GPU NVIDIA ao container
#
# Variáveis de ambiente:
#   GPU=1            adiciona --device nvidia.com/gpu=all (requer driver NVIDIA,
#                    nvidia-container-toolkit e a spec CDI no host)
#   REUTILIZAR_MODELOS_HOST=1  reutiliza ~/.ollama do host em vez do volume
#
# Pré-requisito: podman instalado.

set -euo pipefail

REDE="botnet"
CONTAINER_OLLAMA="ollama"
VOLUME_MODELOS="${VOLUME_MODELOS:-ollama}"
MODELO="${1:-${OLLAMA_MODEL:-gemma4:12b}}"

if ! command -v podman >/dev/null 2>&1; then
    echo "Erro: 'podman' não encontrado no PATH." >&2
    exit 1
fi

# 1) Rede privada (idempotente)
if podman network exists "$REDE"; then
    echo "Rede '$REDE' já existe."
else
    echo "Criando rede '$REDE'..."
    podman network create "$REDE"
fi

# 2) Container do Ollama (idempotente)
RUN_ARGS=(-d --name "$CONTAINER_OLLAMA" --network "$REDE" --restart unless-stopped)
if [[ "${GPU:-0}" == "1" ]]; then
    RUN_ARGS+=(--device nvidia.com/gpu=all)
    echo "-> GPU habilitada (--device nvidia.com/gpu=all)."
fi

if podman container exists "$CONTAINER_OLLAMA"; then
    echo "Container '$CONTAINER_OLLAMA' já existe; iniciando se estiver parado..."
    podman start "$CONTAINER_OLLAMA" || true
else
    echo "Subindo container '$CONTAINER_OLLAMA' na rede '$REDE'..."
    if [[ "${REUTILIZAR_MODELOS_HOST:-0}" == "1" ]]; then
        podman run "${RUN_ARGS[@]}" \
            -v "$HOME/.ollama:/root/.ollama:Z" \
            ollama/ollama
        echo "-> Reutilizando modelos do host em ~/.ollama."
    else
        podman run "${RUN_ARGS[@]}" \
            -v "$VOLUME_MODELOS:/root/.ollama" \
            ollama/ollama
    fi
fi

# 3) Modelo
echo "Garantindo modelo '$MODELO'..."
podman exec "$CONTAINER_OLLAMA" ollama pull "$MODELO"

# 4) Status e próximos passos
cat <<EOF

Ollama em container pronto: http://$CONTAINER_OLLAMA:11434 (rede '$REDE').

Para recriar o container com outra configuração (ex.: GPU=1), remova-o antes:
  podman stop ollama && podman rm ollama
(Os modelos ficam no volume/bind mount e não se perdem.)

Próximos passos (manuais, ver README):
1. No .env: OLLAMA_BASE_URL=http://$CONTAINER_OLLAMA:11434
   (mantenha OLLAMA_MODEL=$MODELO)
2. Suba o bot na mesma rede:
     podman run -d --name automatizacao-ti --network $REDE \
       --env-file .env -v automatizacao_ti_data:/app/data \
       --restart unless-stopped automatizacao-ti
   (se já existe um container do bot, pare e remova antes:
    podman stop automatizacao-ti && podman rm automatizacao-ti)
3. Teste a conectividade (esperado 200):
     podman exec automatizacao-ti python -c "import httpx; r = httpx.get('http://$CONTAINER_OLLAMA:11434/api/tags', timeout=5); print(r.status_code)"
EOF