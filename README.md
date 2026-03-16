# JMJ2027 Bot

Bot de monitorização de notícias das **Jornadas Mundiais da Juventude Seul 2027**. Corre como container Docker e envia notificações automáticas para o Telegram quando há novidades em [wydseoul.org](https://wydseoul.org/pt/news/notice).

## O que monitoriza

| Secção | URL |
|---|---|
| Avisos | `wydseoul.org/pt/news/notice` |
| Notícias da JMJ | `wydseoul.org/pt/news/pressrelease` |

## Comportamento

| Trigger | Acção |
|---|---|
| Todos os dias às **10:00** (hora de Lisboa) | Verifica se há notícias novas e envia uma mensagem por cada notícia inédita |
| Domingo às **12:00** (hora de Lisboa) | Envia um resumo semanal com todas as notícias da semana — só se houver |
| Sem novidades | Silêncio — nenhuma mensagem é enviada |

O bot guarda o estado em disco (`state.json`) para nunca duplicar notificações entre reinicios.

## Exemplos de mensagens

**Nova notícia:**
```
🔔 Nova notícia JMJ Seul 2027

📂 Avisos
📰 Resultados da primeira fase de avaliação do Hino Oficial
📅 2026-02-14
```

**Resumo semanal:**
```
📋 Resumo Semanal JMJ Seul 2027
Semana de 09/03 a 15/03/2026

3 notícias esta semana:

📂 Avisos
• A peregrinação da Cruz na Diocese de Chuncheon — 2026-02-19
• Cuidado com sites falsos — 2026-02-10

📂 Notícias da JMJ
• JMJ Seul 2027 divulga a sua oração oficial — 2026-02-12
```

## Pré-requisitos

- Docker + Docker Compose
- Bot Telegram criado via [@BotFather](https://t.me/BotFather)
- Chat ID do teu chat ou grupo Telegram

## Instalação standalone

### 1. Clonar o repositório

```bash
git clone <repo-url> /opt/jmj2027
cd /opt/jmj2027
```

### 2. Configurar credenciais

```bash
cp .env.example .env
nano .env
```

```env
TELEGRAM_BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=xxxxxxxxxx
```

> Para obter o `TELEGRAM_CHAT_ID`, envia uma mensagem ao bot e consulta:
> `https://api.telegram.org/bot<TOKEN>/getUpdates`

### 3. Iniciar

```bash
docker compose up -d --build
```

### 4. Verificar logs

```bash
docker compose logs -f
```

Se tudo estiver correto, recebes no Telegram: **"✅ JMJ2027 Bot iniciado"**.

## Instalação como parte do homeserver

Este serviço está integrado no `docker-compose.yml` central do [homeserver](../homeserver). Para arrancar apenas este serviço:

```bash
cd homeserver
docker compose up -d --build jmj2027
```

## Estrutura do projeto

```
jmj2027/
├── Dockerfile
├── requirements.txt
├── .env                  ← credenciais (não commitar)
├── .env.example
├── .gitignore
└── monitor/
    ├── main.py           ← loop principal e scheduler (10h diário, domingo 12h)
    ├── scraper.py        ← scraping com requests + BeautifulSoup
    ├── state.py          ← persistência de IDs vistos e notícias semanais
    ├── telegram.py       ← envio de mensagens via HTTP API
    └── config.py         ← carregamento de variáveis de ambiente
```

## Configuração

Toda a configuração é feita via variáveis de ambiente no `.env`:

| Variável | Obrigatória | Descrição |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | Token do bot (obtido via @BotFather) |
| `TELEGRAM_CHAT_ID` | ✅ | ID do chat para onde enviar as mensagens |
| `STATE_PATH` | ❌ | Caminho do ficheiro de estado (default: `/app/data/state.json`) |

O timezone está fixo a `Europe/Lisbon` no `docker-compose.yml` via `TZ=Europe/Lisbon`.

## Estado persistido

O ficheiro `state.json` (no volume Docker `jmj2027_data`) guarda:

- **`seen_ids`** — IDs de todas as notícias já enviadas, para evitar duplicados
- **`weekly_news`** — notícias acumuladas desde o último resumo de domingo
- **`last_daily`** / **`last_weekly`** — datas da última execução de cada agendamento

## Nota sobre JavaScript rendering

O site wydseoul.org é servidor-renderizado (SSR). Se nos logs aparecer o aviso _"0 itens encontrados — o site pode requerer JavaScript"_, é sinal de que o site mudou para renderização client-side e será necessário migrar o scraper para [Playwright](https://playwright.dev/).

## Segurança

O `.env` com as credenciais do Telegram **nunca deve ser commitado**. Está incluído no `.gitignore`.
