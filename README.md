# Automação de Solicitações de Suporte

Automação desenvolvida para a disciplina de Sistemas de Informação com o objetivo de automatizar o recebimento e a triagem de solicitações de suporte de TI.

O usuário envia uma solicitação através do Telegram. A aplicação utiliza inteligência artificial para interpretar a mensagem, classificar o chamado e determinar sua prioridade e equipe responsável. Os dados são então armazenados em um banco SQLite, um protocolo é retornado ao usuário e o chamado é encaminhado para o grupo do Telegram da equipe responsável.

## Fluxo da automação

```text
Telegram
   ↓
Python
   ↓
Gemini
   ↓
Classificação (categoria, prioridade, resumo, equipe)
   ↓
SQLite (chamado + equipe responsável)
   ↓
Confirmação para o solicitante
   ↓
Encaminhamento para o grupo da equipe no Telegram
```

## Como rodar com Docker ou Podman

O projeto inclui um `Dockerfile`. Os comandos abaixo funcionam tanto com `docker` quanto com `podman` (as interfaces de linha de comando são compatíveis).

### 1. Configurar as variáveis de ambiente

Copie o arquivo de exemplo e preencha os valores reais:

```bash
cp .example.env .env
# edite o .env: informe o TELEGRAM_BOT_TOKEN e o GEMINI_API_KEY
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

## Equipes e roteamento

As equipes e os IDs dos grupos do Telegram ficam centralizados na tabela `equipes` do banco SQLite. O código apenas consulta o `telegram_chat_id` da equipe identificada pela IA para encaminhar o chamado — nenhum ID de grupo fica hardcoded no código.

Na primeira execução, as equipes `SUPORTE`, `INFRAESTRUTURA` e `DESENVOLVIMENTO` são criadas com `telegram_chat_id` vazio. Para configurar o ID real de cada grupo, informe os `chat_id` nas variáveis de ambiente do `.env` — o script `src/configurar_equipes.py` roda no início do container e aplica os valores na tabela `equipes`:

```bash
EQUIPE_SUPORTE_CHAT_ID=-1001234567890
EQUIPE_INFRAESTRUTURA_CHAT_ID=-1001234567890
EQUIPE_DESENVOLVIMENTO_CHAT_ID=-1001234567890
```

1. Crie o grupo no Telegram e adicione o bot como membro.
2. Obtenha o `chat_id` do grupo (por exemplo, `-1001234567890`).
3. Descomente e preencha as variáveis no `.env` e suba o container.

Alternativamente, é possível atualizar diretamente o banco `/app/data/automation.db`:

```sql
UPDATE equipes
SET telegram_chat_id = '-1001234567890'
WHERE nome = 'SUPORTE';
```

Os `chat_id` dos exemplos são fictícios — substitua pelos IDs reais. Se uma equipe não existir, estiver inativa ou não tiver `telegram_chat_id`, o chamado é salvo normalmente, porém não é encaminhado: o erro é registrado no log e o solicitante é informado.
