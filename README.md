# Automação de Solicitações de Suporte

Automação desenvolvida para a disciplina de Sistemas de Informação com o objetivo de automatizar o recebimento e a triagem de solicitações de suporte de TI.

O usuário envia uma solicitação através do Telegram. A aplicação utiliza inteligência artificial para interpretar a mensagem, classificar o chamado e determinar sua prioridade e equipe responsável. Os dados são então armazenados em um banco SQLite e um protocolo é retornado ao usuário.

## Fluxo da automação

```text
Telegram
   ↓
Python
   ↓
Gemini
   ↓
Classificação da solicitação
   ↓
SQLite
   ↓
Resposta no Telegram
