import pytest

from fastapi import BackgroundTasks

from fastapi.testclient import TestClient

from dependencies.conversation import get_conversation_store

from dependencies.cordination import get_coordinator

from fake_analyser_api.main import app

from services.conversation.state import ConversationState, MemoryConversationStore

from services.cordination.cordination import MemoryCoordinator

from services.evolution.messages import get_template

from services.handlers import conversation

from services.handlers.messages import dispatch_message


JID = "5511999999999@s.whatsapp.net"


def upsert(jid=JID, message_id="MSG-1", message=None, from_me=False, **data) -> dict:
    return {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": jid, "fromMe": from_me, "id": message_id},
            "pushName": "Maria",
            "message": {"conversation": "oi"} if message is None else message,
            **data,
        },
    }


@pytest.fixture
def sent(monkeypatch):
    messages: list[tuple[str, str]] = []

    async def fake_send_text_message(instance_name, number, text, client):
        messages.append((number, text))
        return {}

    async def fake_analyse_news(notice, client):
        return "Análise do Gemini"

    # Nenhuma chamada real à Evolution, à Brave ou ao Gemini
    monkeypatch.setattr(conversation, "send_text_message", fake_send_text_message)
    monkeypatch.setattr(conversation, "analyse_news", fake_analyse_news)
    return messages


@pytest.fixture
def coord():
    return MemoryCoordinator()


@pytest.fixture
def store():
    return MemoryConversationStore()


# ---------- dispatch_message ----------

@pytest.mark.anyio
@pytest.mark.parametrize("payload", [
    upsert(jid="120363000000000000@g.us"),
    upsert(jid="status@broadcast"),
    upsert(jid="120363000000000000@newsletter"),
    upsert(from_me=True),
    upsert(jid=None),
    upsert(message_id=None),
    {"event": "messages.upsert"},
    {"event": "messages.upsert", "data": None},
    {"event": "messages.upsert", "data": {"key": None}},
], ids=["grupo", "status", "canal", "from_me", "sem_jid", "sem_id", "sem_data", "data_none", "key_none"])
async def test_eventos_ignorados_nao_agendam_processamento(payload, coord, store, sent):
    tasks = BackgroundTasks()

    await dispatch_message(payload, None, coord, store, tasks)

    assert tasks.tasks == []


@pytest.mark.anyio
async def test_mensagem_de_usuario_responde_saudacao_e_menu(coord, store, sent):
    tasks = BackgroundTasks()

    await dispatch_message(upsert(), None, coord, store, tasks)
    await tasks()

    assert len(sent) == 1
    assert sent[0][0] == JID
    assert get_template("menu") in sent[0][1]


@pytest.mark.anyio
@pytest.mark.parametrize("message", [None, {}], ids=["message_none", "message_vazio"])
async def test_message_vazio_nao_quebra_nem_responde(message, coord, store, sent):
    payload = upsert()
    payload["data"]["message"] = message
    tasks = BackgroundTasks()

    await dispatch_message(payload, None, coord, store, tasks)
    await tasks()

    assert sent == []


@pytest.mark.anyio
async def test_evento_duplicado_e_processado_uma_vez(coord, store, sent):
    for _ in range(2):
        tasks = BackgroundTasks()
        await dispatch_message(upsert(message_id="REPETIDO"), None, coord, store, tasks)
        await tasks()

    assert len(sent) == 1


@pytest.mark.anyio
async def test_link_em_extended_text_e_analisado(coord, store, sent):
    store.set_awaiting(JID)
    payload = upsert(message={"extendedTextMessage": {"text": "https://exemplo.com/noticia"}})
    tasks = BackgroundTasks()

    await dispatch_message(payload, None, coord, store, tasks)
    await tasks()

    assert [text for _, text in sent] == [
        get_template("text_analysis_message"),
        "Análise do Gemini",
        get_template("analysis_done"),
    ]
    assert store.get_state(JID) is ConversationState.IDLE


# ---------- rota /messages/new-message/ ----------

@pytest.fixture
def api(coord, store, sent):
    app.dependency_overrides[get_coordinator] = lambda: coord
    app.dependency_overrides[get_conversation_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_rota_webhook_processa_mensagem(api, sent):
    response = api.post("/messages/new-message/", json=upsert())

    assert response.status_code == 200
    assert len(sent) == 1
    assert "Olá Maria" in sent[0][1]


def test_rota_webhook_fluxo_opcao_1_e_noticia(api, store, sent):
    api.post("/messages/new-message/", json=upsert(message={"conversation": "1"}, message_id="A"))
    assert store.get_state(JID) is ConversationState.AWAITING_NEWS

    api.post("/messages/new-message/", json=upsert(message={"conversation": "Notícia"}, message_id="B"))

    assert sent[-1][1] == get_template("analysis_done")
    assert store.get_state(JID) is ConversationState.IDLE


def test_rota_webhook_ignora_outros_eventos(api, sent):
    response = api.post("/messages/new-message/", json={"event": "messages.update", "data": {}})

    assert response.status_code == 200
    assert sent == []
