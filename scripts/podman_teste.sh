#!/usr/bin/env bash
#
# Builda o estágio "test" do Dockerfile e roda a suíte pytest dentro do
# container (mesma imagem base e mesmas dependências da produção).
#
# Uso:
#   bash scripts/podman_teste.sh                       # build + suíte completa
#   bash scripts/podman_teste.sh -v tests/test_bot.py  # args adicionais do pytest
#   bash scripts/podman_teste.sh --montar-codigo       # monta o código local em
#                                                      # /app (sem rebuild a cada
#                                                      # mudança)
#   SELINUX=1 bash scripts/podman_teste.sh --montar-codigo
#
# Variáveis de ambiente:
#   SELINUX=1  acrescenta ":Z" ao bind mount (necessário em Fedora e similares)

set -euo pipefail

IMAGEM="automatizacao-ti:test"
MONTAR_CODIGO=0
ARGS_PYTEST=()

usage() {
    cat <<'EOF'
Sobe a suíte de testes em container (estágio "test" do Dockerfile).

Uso:
  bash scripts/podman_teste.sh                       # build + suíte completa
  bash scripts/podman_teste.sh -v tests/test_bot.py  # args adicionais do pytest
  bash scripts/podman_teste.sh --montar-codigo       # monta o código local em
                                                     # /app (sem rebuild a cada
                                                     # mudança)
  SELINUX=1 bash scripts/podman_teste.sh --montar-codigo

Variáveis de ambiente:
  SELINUX=1  acrescenta ":Z" ao bind mount (necessário em Fedora e similares)
EOF
}

for arg in "$@"; do
    case "$arg" in
        --montar-codigo)
            MONTAR_CODIGO=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            ARGS_PYTEST+=("$arg")
            ;;
    esac
done

echo ">> Construindo imagem de teste ($IMAGEM)..."
podman build -t "$IMAGEM" --target test .

RUN_ARGS=(run --rm)
if [[ "$MONTAR_CODIGO" == "1" ]]; then
    MOUNT="$(pwd):/app"
    if [[ "${SELINUX:-0}" == "1" ]]; then
        MOUNT="${MOUNT}:Z"
    fi
    RUN_ARGS+=(-v "$MOUNT")
    echo ">> Código local montado em /app (mudanças valem sem rebuild)."
fi

if [[ "${#ARGS_PYTEST[@]}" -gt 0 ]]; then
    echo ">> pytest ${ARGS_PYTEST[*]}"
    podman "${RUN_ARGS[@]}" "$IMAGEM" python -m pytest "${ARGS_PYTEST[@]}"
else
    podman "${RUN_ARGS[@]}" "$IMAGEM"
fi