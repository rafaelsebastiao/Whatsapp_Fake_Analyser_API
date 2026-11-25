from fastapi import BackgroundTasks

from services.conversation.state import MemoryConversationStore

from services.cordination.cordination import MemoryCoordinator

from services.handlers.conversation import handle_conversation

from services.handlers.parser import parse_message


# Grupos, status (status@broadcast), listas de transmissão e canais não são atendidos
IGNORED_JID_SUFFIXES = ("@g.us", "@broadcast", "@newsletter")


async def dispatch_message(
    payload: dict,
    client,
    coord: MemoryCoordinator,
    store: MemoryConversationStore,
    background_tasks: BackgroundTasks,
):
    data = payload.get("data") or {}
    key = data.get("key") or {}
    jid = key.get("remoteJid")
    message_id = key.get("id")

    # ignora mensagens enviadas pelo próprio bot e eventos sem identificação
    if key.get("fromMe") or not jid or not message_id:
        return

    # ignora grupos, status e canais
    if jid.endswith(IGNORED_JID_SUFFIXES):
        return

    # ignora evento repetido da Evolution
    if await coord.is_duplicate(message_id):
        return

    # True só para quem deve iniciar o processamento deste usuário
    if await coord.enqueue(jid, payload):
        background_tasks.add_task(
            coord.drain,
            jid,
            lambda p: handle_message_upsert(p, client, store),
        )


async def handle_message_upsert(payload: dict, client, store: MemoryConversationStore):
    # Captura do json retornado pelo webhook assim que é detectado uma mensagem para o bot
    data = payload.get("data") or {}

    # Captura do número de telefone
    remote_jid = (data.get("key") or {}).get("remoteJid")

    # Captura do nome de usuário
    user_name = data.get("pushName")

    # Tipo e conteúdo da mensagem (texto, imagem, não suportada ou ignorada)
    parsed = parse_message(data)

    await handle_conversation(remote_jid, user_name, parsed, store, client)
