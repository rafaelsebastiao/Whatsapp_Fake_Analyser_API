import anyio

import pytest

from fastapi import BackgroundTasks

from services.conversation.state import MemoryConversationStore

from services.cordination.cordination import MemoryCoordinator

from services.handlers import messages


pytestmark = pytest.mark.anyio

JID = "5511999999999@s.whatsapp.net"


def upsert(message_id: str, text: str, jid: str = JID) -> dict:
    return {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": jid, "fromMe": False, "id": message_id},
            "message": {"conversation": text},
        },
    }


# ---------- deduplicação ----------

async def test_evento_duplicado_e_detectado():
    coord = MemoryCoordinator()

    assert await coord.is_duplicate("MSG-1") is False
    assert await coord.is_duplicate("MSG-1") is True
    assert await coord.is_duplicate("MSG-2") is False


async def test_evento_repetido_depois_do_ttl_nao_e_duplicado():
    coord = MemoryCoordinator(dedup_ttl=0)

    assert await coord.is_duplicate("MSG-1") is False
    assert await coord.is_duplicate("MSG-1") is False


# ---------- fila por usuário ----------

async def test_so_o_primeiro_enqueue_inicia_o_processamento():
    coord = MemoryCoordinator()

    assert await coord.enqueue(JID, {"n": 1}) is True
    assert await coord.enqueue(JID, {"n": 2}) is False
    # Outro usuário tem a própria fila
    assert await coord.enqueue("outro@s.whatsapp.net", {"n": 1}) is True


async def test_drain_processa_em_ordem_e_libera_o_usuario():
    coord = MemoryCoordinator()
    handled = []

    async def handler(payload):
        handled.append(payload["n"])

    await coord.enqueue(JID, {"n": 1})
    await coord.enqueue(JID, {"n": 2})
    await coord.drain(JID, handler)

    assert handled == [1, 2]
    # Fila vazia: a próxima mensagem inicia um novo processamento
    assert await coord.enqueue(JID, {"n": 3}) is True


async def test_erro_numa_mensagem_nao_trava_a_fila():
    coord = MemoryCoordinator()
    handled = []

    async def handler(payload):
        if payload["n"] == 1:
            raise RuntimeError("falha na Evolution")
        handled.append(payload["n"])

    await coord.enqueue(JID, {"n": 1})
    await coord.enqueue(JID, {"n": 2})
    await coord.drain(JID, handler)

    assert handled == [2]
    assert await coord.enqueue(JID, {"n": 3}) is True


async def test_mensagens_simultaneas_do_mesmo_usuario_sao_processadas_em_sequencia():
    coord = MemoryCoordinator()
    events = []
    first_started = anyio.Event()

    async def handler(payload):
        events.append(f"inicio {payload['n']}")
        first_started.set()
        await anyio.sleep(0.05)  # simula a espera pela Evolution/Gemini
        events.append(f"fim {payload['n']}")

    async def receive(n):
        if await coord.enqueue(JID, {"n": n}):
            await coord.drain(JID, handler)

    async with anyio.create_task_group() as tg:
        tg.start_soon(receive, 1)
        await first_started.wait()
        # Chegam enquanto a primeira ainda está sendo processada
        tg.start_soon(receive, 2)
        tg.start_soon(receive, 3)

    assert events == ["inicio 1", "fim 1", "inicio 2", "fim 2", "inicio 3", "fim 3"]


# ---------- integração com o webhook ----------

async def test_dispatch_mensagens_simultaneas_respeitam_a_ordem_dos_estados(monkeypatch):
    coord = MemoryCoordinator()
    store = MemoryConversationStore()
    processed = []

    async def fake_handle(payload, client, store):
        text = payload["data"]["message"]["conversation"]
        processed.append(text)
        await anyio.sleep(0.01)

    monkeypatch.setattr(messages, "handle_message_upsert", fake_handle)

    tasks = BackgroundTasks()
    # "1" e a notícia chegam quase juntas; só a primeira agenda o processamento
    await messages.dispatch_message(upsert("A", "1"), None, coord, store, tasks)
    await messages.dispatch_message(upsert("B", "Notícia"), None, coord, store, tasks)
    await messages.dispatch_message(upsert("B", "Notícia"), None, coord, store, tasks)  # duplicada

    assert len(tasks.tasks) == 1
    await tasks()

    assert processed == ["1", "Notícia"]
