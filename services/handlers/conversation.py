from httpx import AsyncClient

from services.ai.genai import text_analisys

from services.conversation.state import ConversationState, MemoryConversationStore

from services.evolution.messages import send_text_message, get_template

from services.handlers.parser import MessageType, ParsedMessage

from settings.settings import Settings


chatbot_instance_name = Settings().CHATBOT_INSTANCE_NAME

# Menu em texto numerado (botões não são exibidos pelo WhatsApp): opções 1, 2 e 3 em handle_idle
CANCEL_WORDS = {"0", "menu"}


# Máquina de estados da conversa. O MemoryCoordinator já processa as mensagens de cada
# usuário em sequência, então não há duas transições do mesmo usuário ao mesmo tempo.
async def handle_conversation(
    jid: str,
    user_name: str | None,
    parsed: ParsedMessage,
    store: MemoryConversationStore,
    client: AsyncClient,
):
    # Reações, mensagens apagadas/editadas e message vazio não mudam nada
    if parsed.type is MessageType.IGNORED:
        return

    if store.get_state(jid) is ConversationState.AWAITING_NEWS:
        await handle_awaiting_news(jid, parsed, store, client)
    else:
        await handle_idle(jid, user_name, parsed, store, client)


# OCIOSO: qualquer mensagem que não seja uma opção recebe saudação + menu
async def handle_idle(
    jid: str,
    user_name: str | None,
    parsed: ParsedMessage,
    store: MemoryConversationStore,
    client: AsyncClient,
):
    option = parsed.text if parsed.type is MessageType.TEXT else None

    match option:
        case "1":
            store.set_awaiting(jid)
            await send(jid, get_template("request_text"), client)

        case "2":
            # TODO: análise de imagem. Até lá, avisa e continua OCIOSO
            await send(jid, join(get_template("image_in_development"), get_template("menu")), client)

        case "3":
            await send(jid, join(get_template("how_it_works"), get_template("menu")), client)

        case _:
            await send(jid, join(get_greeting(user_name), get_template("menu")), client)


# AGUARDANDO_NOTICIA: analisa o texto recebido, sem limite de tamanho
async def handle_awaiting_news(
    jid: str,
    parsed: ParsedMessage,
    store: MemoryConversationStore,
    client: AsyncClient,
):
    match parsed.type:
        case MessageType.TEXT if parsed.text.lower() in CANCEL_WORDS:
            store.reset(jid)
            await send(jid, join(get_template("analysis_canceled"), get_template("menu")), client)

        case MessageType.TEXT:
            await send(jid, get_template("text_analysis_message"), client)

            analysis = await text_analisys(parsed.text)

            if analysis is None:
                # Continua aguardando e reinicia os 10 minutos para o usuário reenviar
                store.set_awaiting(jid)
                await send(jid, get_template("analysis_failed"), client)
                return

            await send(jid, analysis, client)
            await send(jid, get_template("analysis_done"), client)
            store.reset(jid)

        case MessageType.IMAGE:
            # TODO: análise de imagem (template image_analysis_message)
            await send(jid, get_template("image_not_supported"), client)

        case _:
            await send(jid, get_template("prohibited_message_type"), client)


def get_greeting(user_name: str | None) -> str:
    hello = f'🤖 Olá {user_name}, tudo bem?' if user_name else '🤖 Olá, tudo bem?'
    return f'{hello}\n{get_template("greetings")}'


# Junta textos numa única mensagem do WhatsApp
def join(*texts: str) -> str:
    return "\n\n".join(texts)


async def send(jid: str, text: str, client: AsyncClient):
    await send_text_message(
        instance_name=chatbot_instance_name,
        number=jid,
        text=text,
        client=client
    )
