# Automação de Solicitações de Suporte

Automação desenvolvida para a disciplina de Sistemas de Informação com o objetivo de automatizar o recebimento e a triagem de solicitações de suporte de TI.

O usuário envia uma solicitação através do Telegram. A aplicação utiliza inteligência artificial para interpretar a mensagem, classificar o chamado e determinar sua prioridade e equipe responsável. Os dados são então armazenados em um banco SQLite, um protocolo é retornado ao usuário e o chamado é encaminhado para o grupo do Telegram da equipe responsável.

A classificação pode ser feita por **IA local (Ollama)** ou pela **API do Google Gemini**, escolhida por uma variável de ambiente — sem nenhuma mudança nos casos de uso.

## Arquitetura

O projeto segue a **Arquitetura Hexagonal (Ports and Adapters)**:

- **Domínio** (`src/domain`) — entidades e regras de negócio (`Equipe`, `Chamado`, `AnaliseSolicitacao`). Não importa nenhuma tecnologia.
- **Aplicação** (`src/application`) — **portas** (interfaces) e **casos de uso**. A aplicação depende apenas das portas, nunca de Ollama, Gemini, Telegram ou SQLite.
- **Adapters** (`src/adapters`) — implementações concretas das portas:
  - **Entrada:** Telegram (handlers + textos).
  - **Saída:** IA (`ollama`, `gemini`) e persistência (`sqlite`).
- **Composição** (`src/config`, `src/main.py`) — ponto único que lê o ambiente e liga o adapter escolhido às portas.

```text
Telegram
   ↓ (adapter de entrada)
Caso de uso  ──►  porta AIProvider  ──►  Ollama | Gemini
   │
   └──────────►  porta AutomationRepository ──►  SQLite
```

A seleção do provedor de IA acontece em **um único ponto**: `src/config/composition.py`, guiada pela variável `AI_PROVIDER`.

## Fluxo da automação

```text
Telegram
   ↓
Caso de uso: processar solicitação
   ↓
Provedor de IA (Ollama ou Gemini)
   ↓
Classificação (categoria, prioridade, resumo, equipe)
   ↓
SQLite (chamado + equipe responsável)
   ↓
Confirmação para o solicitante
   ↓
Encaminhamento para o grupo da equipe no Telegram
```

Se a classificação falhar (provedor indisponível ou resposta inválida), o chamado é salvo e atribuído por padrão à equipe **SUPORTE** — o que é uma regra de negócio, e por isso vive no caso de uso.

## Estrutura do projeto

```text
src/
├── main.py                              # composition root
├── configurar_equipes.py                # aplica os chat_ids das equipes no start
├── config/
│   ├── settings.py                      # única leitura de variáveis de ambiente
│   └── composition.py                   # seleção do provider (ollama|gemini)
├── domain/
│   ├── entities.py                      # Equipe, Chamado + regras
│   └── value_objects.py                 # AnaliseSolicitacao (contrato com a IA)
├── application/
│   ├── ports/
│   │   ├── ai_provider.py               # AIProvider (Protocol) + erros de IA
│   │   └── repository.py                # AutomationRepository (Protocol)
│   └── use_cases/
│       ├── processar_solicitacao.py     # classifica, persiste, roteia
│       └── consultar_chamado.py         # /consultar <protocolo>
└── adapters/
    ├── inbound/telegram/                # bot.py (handlers) + messages.py (textos)
    └── outbound/
        ├── ai/ollama.py                 # OllamaAIProvider (IA local)
        ├── ai/gemini.py                 # GeminiAIProvider (API do Google)
        └── persistence/sqlite/          # database.py (schema) + repository.py

scripts/                                 # utilitários Podman: ollama, testes e dev
tests/                                   # suíte pytest (sem serviços externos)
```

## Como rodar com Docker ou Podman

O projeto inclui um `Dockerfile`. Os comandos abaixo funcionam tanto com `docker` quanto com `podman` (as interfaces de linha de comando são compatíveis).

### 1. Configurar as variáveis de ambiente

Copie o arquivo de exemplo e preencha os valores reais:

```bash
cp .example.env .env
# edite o .env: informe AI_PROVIDER e as credenciais do provedor escolhido
```

### 2. Construir a imagem

```bash
docker build -t automatizacao-ti .
# com Podman:
podman build -t automatizacao-ti .
```

### 3. Executar o container

O banco SQLite fica em `/app/data/automation.db`. Para que os chamados e as configurações das equipes sejam mantidos entre execuções, monte um volume nesse diretório:

```bash
docker run -d \
  --name automatizacao-ti \
  --env-file .env \
  -v automatizacao_ti_data:/app/data \
  --restart unless-stopped \
  automatizacao-ti
```

Com Podman o comando é o mesmo:

```bash
podman run -d \
  --name automatizacao-ti \
  --env-file .env \
  -v automatizacao_ti_data:/app/data \
  --restart unless-stopped \
  automatizacao-ti
```

> `-v automatizacao_ti_data:/app/data` cria um volume nomeado gerenciado pelo container. Se preferir, use um bind mount apontando para uma pasta do host, por exemplo `-v "$(pwd)/data:/app/data"`. Em sistemas com SELinux (padrão em Fedora), acrescente `:Z` ao final do caminho em bind mounts: `-v "$(pwd)/data:/app/data:Z"`.

> **Dica (desenvolvimento):** o script `scripts/podman_dev.sh` automatiza os passos 2–4 — constrói a imagem, substitui o container (nome padrão `automatizacao-ti`) e oferece `--build-only`, `--logs` e `--remove`. No cenário da Opção B (Ollama em container), rode com `REDE=botnet bash scripts/podman_dev.sh` para colocar o bot na mesma rede. Com o **Ollama nativo no host**, use `REDE=host bash scripts/podman_dev.sh` (com `OLLAMA_BASE_URL=http://localhost:11434` no `.env`) — o `localhost` do bot passa a ser o da máquina, sem expor `0.0.0.0`.

### 4. Acompanhar o bot

```bash
docker logs -f automatizacao-ti
# com Podman:
podman logs -f automatizacao-ti
```

Para parar e remover o container:

```bash
docker stop automatizacao-ti && docker rm automatizacao-ti
```

Após a primeira execução, siga a seção [Equipes e roteamento](#equipes-e-roteamento) para configurar os IDs dos grupos no banco.

### Requisito de rede

O bot precisa de acesso HTTPS (porta 443) a `https://api.telegram.org`. Se a sua rede bloquear o Telegram — comportamento que aparece como timeout de conexão, sem erro de código — o bot não inicia. Nesse caso, teste em outra rede, use uma VPN ou defina `HTTPS_PROXY` no `.env`.

## Escolhendo o provedor de IA

A variável `AI_PROVIDER` aceita dois valores:

| Valor    | Provedor                | Variáveis necessárias                  |
|----------|-------------------------|----------------------------------------|
| `ollama` | IA local (Ollama)       | `OLLAMA_BASE_URL`, `OLLAMA_MODEL`      |
| `gemini` | API do Google Gemini    | `GEMINI_API_KEY`, `GEMINI_MODEL`       |

O padrão é `gemini` (para não quebrar configurações existentes). A troca de provedor é feita **apenas** no `.env` — nenhum código precisa mudar.

### Com Ollama (IA local)

```bash
# .env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:4b
```

Se a aplicação roda em container e o Ollama roda no host, use `host.containers.internal` (Podman) ou o IP da máquina:

```bash
OLLAMA_BASE_URL=http://host.containers.internal:11434
```

O modelo indicado em `OLLAMA_MODEL` precisa estar baixado no Ollama (`ollama pull qwen3.5:4b`).

#### Ollama em container (mesma rede do bot)

Alternativa que **não exige expor o Ollama do host** (`0.0.0.0`): o Ollama roda em um container Podman na mesma rede privada do bot (`botnet`). O bot acessa o Ollama pelo nome do container (`http://ollama:11434`) e nenhuma porta é publicada no host.

Existe um script que automatiza a criação da rede, do container e o download do modelo:

```bash
bash scripts/subir_ollama_container.sh                                # modelo padrão qwen3.5:4b
bash scripts/subir_ollama_container.sh qwen3.5:4b                     # modelo específico
REUTILIZAR_MODELOS_HOST=1 bash scripts/subir_ollama_container.sh      # reaproveita ~/.ollama do host
GPU=1 bash scripts/subir_ollama_container.sh                          # expõe a GPU NVIDIA ao container
```

Para usar GPU NVIDIA (`GPU=1`), o host precisa do driver NVIDIA, do `nvidia-container-toolkit` e da spec CDI (`sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml`). Para confirmar que a placa está em uso, rode `podman exec -it ollama ollama ps` — a coluna PROCESSOR deve mostrar `100% GPU`. Para trocar a configuração do container (ex.: habilitar GPU depois de criado), recrie-o antes: `podman stop ollama && podman rm ollama` (os modelos ficam no volume/bind mount e não se perdem).

Passos manuais equivalentes ao script:

```bash
# 1. Rede privada dos containers
podman network create botnet

# 2. Container do Ollama (modelos isolados no volume "ollama")
#    Para reaproveitar os modelos já baixados no host, use
#    -v "$HOME/.ollama:/root/.ollama:Z" no lugar do volume.
podman run -d \
  --name ollama \
  --network botnet \
  --restart unless-stopped \
  -v ollama:/root/.ollama \
  ollama/ollama

# 3. Modelo (ajuste o nome conforme o OLLAMA_MODEL do .env)
podman exec -it ollama ollama pull qwen3.5:4b
```

No `.env`:

```bash
OLLAMA_BASE_URL=http://ollama:11434
```

Suba o bot na mesma rede:

```bash
podman run -d \
  --name automatizacao-ti \
  --network botnet \
  --env-file .env \
  -v automatizacao_ti_data:/app/data \
  --restart unless-stopped \
  automatizacao-ti
```

Teste rápido da conectividade (esperado `200`):

```bash
podman exec automatizacao-ti python -c "import httpx; r = httpx.get('http://ollama:11434/api/tags', timeout=5); print(r.status_code)"
```

> A imagem oficial do Ollama já escuta nas interfaces internas do container — o requisito de expor `0.0.0.0` no host **não** se aplica a esta opção.

### Com Gemini (API do Google)

```bash
# .env
AI_PROVIDER=gemini
GEMINI_API_KEY=COLOQUE_SUA_CHAVE_AQUI
GEMINI_MODEL=gemini-3.8-flash
```

> A chave da API é usada apenas via variável de ambiente — nunca fica no código, no README ou em logs.

## Testes

A suíte usa apenas fakes e um banco SQLite temporário (arquivo em `tmp_path`) — **nenhum serviço externo** é chamado.

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Os testes cobrem:

- Casos de uso com `FakeAIProvider` e repositório em memória (classificação, fallback para SUPORTE em erro da IA, equipe inexistente, erro de persistência).
- Consulta de chamado pelo protocolo.
- Regras de negócio do domínio (`Equipe.pode_receber`, `Chamado.classificado`).
- Seleção e configuração do provider (`Settings.from_env`, `criar_provider_ia`).
- Adapters de IA: `OllamaAIProvider` (via `httpx.MockTransport`) e `GeminiAIProvider` (com client fake), incluindo comportamento em falha/timeout/resposta inválida.
- Repositório SQLite (salvar, buscar, atualizar, equipes iniciais).

### Rodar os testes no container (Podman/Docker)

O `Dockerfile` tem um estágio `test` separado, que instala as dependências de desenvolvimento (`requirements-dev.txt`) e roda a suíte com a mesma imagem base e as mesmas versões de bibliotecas da produção — garantindo paridade de ambiente sem instalar nada no host:

```bash
podman build -t automatizacao-ti:test --target test .
podman run --rm automatizacao-ti:test
```

Para iterar sobre os testes sem reconstruir a imagem a cada mudança, monte o diretório atual por cima do código copiado (em sistemas com SELinux, acrescente `:Z`):

```bash
podman run --rm -v "$(pwd):/app:Z" automatizacao-ti:test
```

Para facilitar, existe o script `scripts/podman_teste.sh` — ele faz o build do estágio `test` e roda a suíte, com opção de montar o código local para iterar sem reconstruir a imagem a cada mudança:

```bash
bash scripts/podman_teste.sh                            # build + suíte completa
bash scripts/podman_teste.sh -v tests/test_bot.py       # args adicionais do pytest
bash scripts/podman_teste.sh --montar-codigo            # código local montado (sem rebuild)
SELINUX=1 bash scripts/podman_teste.sh --montar-codigo  # em Fedora e similares
```

> A imagem de produção continua enxuta: o estágio final não inclui `pytest` nem a pasta `tests/`.

## Equipes e roteamento

As equipes e os IDs dos grupos do Telegram ficam centralizados na tabela `equipes` do banco SQLite. O código apenas consulta o `telegram_chat_id` da equipe identificada pela IA para encaminhar o chamado — nenhum ID de grupo fica hardcoded no código.

Na primeira execução, as equipes `SUPORTE`, `INFRAESTRUTURA` e `DESENVOLVIMENTO` são criadas com `telegram_chat_id` vazio. Para configurar o ID real de cada grupo, informe os `chat_id` nas variáveis de ambiente do `.env` — o script `src/configurar_equipes.py` roda no início do container e aplica os valores na tabela:

```bash
EQUIPE_SUPORTE_CHAT_ID=-1001234567890
EQUIPE_INFRAESTRUTURA_CHAT_ID=-1001234567890
EQUIPE_DESENVOLVIMENTO_CHAT_ID=-1001234567890
```

Uma equipe só recebe chamados se estiver **ativa** e com **grupo configurado** (`telegram_chat_id` preenchido) — regra em `Equipe.pode_receber()`. Se o grupo não estiver configurado, o chamado é registrado normalmente e o usuário fica com o protocolo, mas o encaminhamento não acontece até o grupo ser configurado.