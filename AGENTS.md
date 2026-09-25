# AGENTS.md

## Escopo do projeto

Este arquivo define as regras para qualquer agente de IA que trabalhe neste projeto.

### Diretório permitido

- Considere a pasta onde este `AGENTS.md` está localizado como a **raiz do projeto**.
- Trabalhe **exclusivamente dentro da pasta raiz do projeto e de seus subdiretórios**.
- Não acesse, leia, modifique, crie ou exclua arquivos fora da pasta raiz do projeto.
- Não navegue para diretórios pai ou para outras pastas do sistema.
- Não procure arquivos ou configurações fora da pasta raiz.
- Não utilize arquivos externos ao projeto como contexto ou dependência sem autorização explícita do usuário.

## Restrições de execução

**NÃO EXECUTE O PROJETO OU QUALQUER CÓDIGO.**

O agente não deve:

- Executar Python.
- Executar scripts.
- Executar comandos do projeto.
- Iniciar servidores.
- Iniciar containers.
- Executar testes.
- Executar linters.
- Executar formatadores.
- Instalar dependências.
- Compilar ou fazer build.
- Fazer requisições para APIs.
- Iniciar ou interagir com o bot do Telegram.
- Fazer chamadas para a API do Gemini.
- Alterar banco de dados através da execução do projeto.

Qualquer comando que execute código ou produza efeitos externos deve ser evitado.

## Restrições de ferramentas

**NÃO UTILIZE FERRAMENTAS PARA EXECUTAR OU ALTERAR O AMBIENTE.**

O agente deve trabalhar somente através da análise e edição dos arquivos do projeto.

Não utilize ferramentas para:

- Executar comandos.
- Executar código.
- Acessar a internet.
- Fazer requisições HTTP.
- Consultar APIs externas.
- Acessar serviços externos.
- Interagir com Docker ou Podman.
- Interagir com bancos de dados externos.
- Alterar configurações do sistema.
- Instalar ou remover pacotes.
- Acessar arquivos fora da raiz do projeto.

Se uma tarefa exigir alguma dessas ações, **não execute a ação**. Explique ao usuário o que precisa ser feito manualmente.

## Alteração de arquivos

Antes de modificar um arquivo:

1. Leia o arquivo para entender o contexto existente.
2. Faça somente as alterações necessárias para atender à solicitação.
3. Preserve o estilo e a estrutura existentes.
4. Não altere arquivos que não sejam relevantes para a tarefa.
5. Não crie arquivos adicionais sem necessidade.

## Dependências

Não instale dependências automaticamente.

Se uma nova dependência for necessária:

1. Informe o nome da dependência.
2. Explique por que ela é necessária.
3. Mostre a alteração necessária no arquivo de dependências.
4. Deixe a instalação para o usuário.

## Variáveis de ambiente e segredos

- Nunca exponha ou substitua valores de API keys, tokens ou outras credenciais.
- Nunca procure credenciais fora da pasta raiz.
- Não altere o arquivo `.env` sem solicitação explícita.
- Não coloque credenciais diretamente no código.
- Preserve o uso de variáveis de ambiente existente no projeto.

## Código

Ao modificar código:

- Prefira soluções simples e legíveis.
- Não introduza abstrações desnecessárias.
- Respeite a arquitetura existente.
- Não reescreva arquivos inteiros quando uma alteração localizada for suficiente.
- Não altere comportamento não relacionado à tarefa solicitada.
- Não adicione funcionalidades que não foram solicitadas.

## Testes e validação

Como o agente está proibido de executar código, testes ou ferramentas:

- Não execute testes.
- Não execute linters.
- Não execute formatadores.
- Não execute o projeto.

Em vez disso, faça apenas uma **análise estática do código** e informe ao usuário quais pontos foram verificados.

## Git

Não execute comandos Git.

Não faça automaticamente:

- `git status`
- `git diff`
- `git add`
- `git commit`
- `git push`
- `git pull`
- `git checkout`
- `git reset`
- ou qualquer outro comando Git.

Se o usuário solicitar uma mensagem de commit, apenas forneça a mensagem.

## Comunicação

Ao finalizar uma tarefa:

- Resuma as alterações realizadas.
- Liste os arquivos modificados.
- Informe qualquer ponto que não pôde ser validado devido às restrições de execução.
- Não alegue que o código foi executado ou testado.
