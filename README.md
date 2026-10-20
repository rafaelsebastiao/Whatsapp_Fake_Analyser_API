# API - Whatsapp Chatbot - Fake Analyser

API intermediária (FastAPI) do chatbot **Fake Analyser**. Ela se comunica com a Evolution API: recebe os webhooks de mensagens do WhatsApp, decide a resposta e envia as mensagens de volta.

A Evolution API (e o banco dela) sobem em **outro repositório**, `fake_analyser_whatsapp_chatbot`. Este projeto não altera a estrutura interna da Evolution, só consome a API dela.

## Visão geral

Dois projetos Docker Compose separados, conectados por uma rede compartilhada.

| Serviço | Repositório / pasta | Container | Porta no PC | Porta interna |
|---|---|---|---|---|
| **API intermediária** (FastAPI) | `fake_analyser` (este) | `fake-analyser-api` | 8000 | 8000 |
| Evolution API | `fake_analyser_whatsapp_chatbot` (outro repo) | `evolution_api` | 8080 | 8080 |
| Banco da Evolution (Postgres) | `fake_analyser_whatsapp_chatbot` (outro repo) | `evolution_db` | não publicada | 5432 |

Ajuste os nomes das pastas se os seus forem diferentes. Todos os comandos abaixo são executados no terminal do WSL, dentro da pasta deste projeto.

### Como os serviços se comunicam

- **Do seu PC** (Insomnia, navegador): `http://localhost:8000` (esta API) e `http://localhost:8080` (Evolution).
- **Entre containers** (rede `fake-analyser-net`): esta API chama a Evolution em `http://evolution-api:8080`, e a Evolution entrega o webhook em `http://fake-analyser-api:8000/messages/new-message/`. Nesse caminho vale a **porta interna** do container, e não `localhost`.

## 1. Pré-requisitos (uma vez só)

1. Docker funcionando no WSL. Para não precisar de `sudo`:
   ```bash
   sudo usermod -aG docker $USER
   ```
   Depois feche e abra o terminal.
2. Rede compartilhada criada (a mesma usada pela Evolution):
   ```bash
   docker network create fake-analyser-net
   ```
   Se responder que já existe, está tudo certo. O `docker-compose.yml` desta API também deve declarar `fake-analyser-net` como rede `external: true`.
3. Evolution API rodando. Siga o README do repositório `fake_analyser_whatsapp_chatbot` antes de subir esta API.

## 2. Configuração de ambiente

Crie um arquivo `.env` na raiz do projeto e preencha as variáveis abaixo. **Não coloque esse arquivo no Git.**

```properties
# URL desta API, vista de dentro da rede Docker (usada na URL do webhook)
OWN_API_URL=http://fake-analyser-api:8000

# Conexão com a Evolution API (WhatsApp), vista de dentro da rede Docker
EVOLUTION_API_URL=http://evolution-api:8080

# Tem que ser IGUAL à AUTHENTICATION_API_KEY do .env da Evolution
EVOLUTION_AUTHENTICATION_API_KEY=<a mesma chave da Evolution>

# Nome da instância que será criada na evolution por esta api (Nome do chatbot)
CHATBOT_INSTANCE_NAME="fake-analyser-chatbot"
```

Rodando a API **fora** do Docker (direto no PC), use `http://localhost:8000` e `http://localhost:8080` nas duas primeiras variáveis.

## 3. Subir

Suba a Evolution primeiro (veja o README dela) e espere aparecer `HTTP - ON: 8080` nos logs. Depois, nesta pasta:

```bash
docker compose up -d --build
docker compose logs -f
```

Procure por `Application startup complete`. O `--build` só é necessário na primeira vez e quando mudar `pyproject.toml` ou o `Dockerfile`.

Confirme que respondem:

- `http://localhost:8000/docs` abre o Swagger desta API.
- `GET http://localhost:8080` (com o header `apikey`) responde da Evolution.

## 4. Conectar o WhatsApp

1. Chame `GET http://localhost:8000/instances/qrcode/`. Se não houver instância, a API cria a `fake-analyser`, gera o QR Code e configura o webhook.
2. No celular: **WhatsApp > Aparelhos conectados > Conectar um aparelho**, e escaneie o QR.
3. Ao conectar, a Evolution dispara `connection.update` (`state: open`) e o bot envia a saudação para o próprio número.

Se a instância já estiver conectada (os dados ficam no volume da Evolution), não é preciso escanear de novo.

## 5. Webhook

O webhook da instância deve ter:

```json
{
  "webhook": {
    "enabled": true,
    "url": "http://fake-analyser-api:8000/messages/new-message/",
    "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE"],
    "headers": { "apikey": "<sua chave>" },
    "base64": true
  }
}
```

- Cada evento é uma string **separada** na lista. `"MESSAGES_UPSERT, CONNECTION_UPDATE"` numa string só dá erro 400.
- O código desta API só cria o webhook quando a instância ainda **não tem nenhum**. Para alterar um webhook existente, sobrescreva com `POST http://localhost:8080/webhook/set/fake-analyser` (header `apikey`) usando o JSON acima.
- Para conferir o que está salvo: `GET http://localhost:8080/webhook/find/fake-analyser`.

## 6. Testes rápidos

- **Rede Evolution → API** (deve responder `{"ok":true}`):
  ```bash
  docker exec evolution_api sh -c "wget -qO- --post-data='{\"teste\":1}' --header='Content-Type: application/json' http://fake-analyser-api:8000/messages/new-message/"
  ```
- **Envio de texto pela Evolution:** `POST http://localhost:8080/message/sendText/fake-analyser` com `{"number": "55DDDNUMERO", "text": "teste"}`.
- **Mensagem recebida:** mande uma mensagem de **outro número** para o número conectado e acompanhe `docker compose logs -f` nesta pasta. Mensagem para si mesmo é um teste pouco confiável.

## 7. Comandos do dia a dia

```bash
docker compose logs -f                  # logs em tempo real (Ctrl+C só sai da visualização)
docker compose restart                  # reinicia sem reler o .env
docker compose up -d --force-recreate   # recria o container (obrigatório após mudar o .env)
docker compose up -d --build            # reconstrói a imagem (após mudar pyproject.toml ou Dockerfile)
docker compose down                     # para e remove os containers
```

A API roda com `--reload` e o código montado como volume, então editar arquivos `.py` recarrega sozinho, sem rebuild.

## 8. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `500 Connection error: The Whatsapp's endpoint is inaccessible` | A API não alcança a Evolution | Conferir `docker exec fake-analyser-api env \| grep URL`: deve ser `http://evolution-api:8080`. Corrigir o `.env` e recriar o container |
| Webhook não chega na API | URL salva antiga, evento não assinado ou containers fora da rede | `GET /webhook/find/fake-analyser`, `docker network inspect fake-analyser-net` e sobrescrever o webhook |
| `400 ... events[0] is not one of enum values` | Eventos juntos numa única string | Separar cada evento como string própria |
| `container name "/fake-analyser-api" is already in use` | Container antigo com o mesmo nome | `docker rm -f fake-analyser-api` e subir de novo |
| `permission denied` no socket do Docker | Usuário fora do grupo `docker` | `sudo usermod -aG docker $USER` e reabrir o terminal |
| Mudou o `.env` e nada mudou | `restart` não relê o `.env` | `docker compose up -d --force-recreate` |
| `Caught handled exception, but response already started` | Exceção HTTP dentro de uma background task | Ver a linha `Falha no handler...` acima dele no log |
