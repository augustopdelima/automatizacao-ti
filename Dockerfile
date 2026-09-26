# Estágio usado apenas para rodar a suíte de testes.
# Build: podman build -t automatizacao-ti:test --target test .
# Run:   podman run --rm automatizacao-ti:test
FROM python:3.13-slim AS test

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# requirements-dev.txt inclui as dependências de produção (via -r) mais o pytest.
COPY requirements.txt requirements-dev.txt ./

RUN pip install --no-cache-dir -r requirements-dev.txt

# O conftest.py da raiz garante o sys.path para os imports src.* e fakes.
COPY conftest.py .
COPY src ./src
COPY tests ./tests

CMD ["python", "-m", "pytest"]


# Imagem de produção: enxuta, sem dependências nem arquivos de teste.
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

RUN mkdir -p /app/data

CMD ["sh", "-c", "python -m src.configurar_equipes && python -m src.main"]