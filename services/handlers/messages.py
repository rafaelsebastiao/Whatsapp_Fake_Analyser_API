import json

from pathlib import Path

from services.evolution.messages import  send_text_message

from settings.settings import Settings

base_path = Path().cwd()

greetings_file_path = base_path / "templates" / "greetings.json"

evolution_api_url = Settings().EVOLUTION_API_URL

evolution_api_key = Settings().EVOLUTION_AUTHENTICATION_API_KEY

chatbot_instance_name = Settings().CHATBOT_INSTANCE_NAME


# Método que lê o json de mensagens padrão que serão enviadas pelo bot
def get_default_message(userName:str) -> str:
    with open(greetings_file_path, 'r', encoding='utf-8') as file:
        content = json.load(file)

    message = f'🤖 Olá {userName}, tudo bem?\n{content["text"]}'
    return message




async def handle_message_upsert(payload: dict, client):
    # Captura do json retornado pelo webhook assim que é detectado uma mensagem para o bot
    data = payload.get("data")

    # Captura do número de telefone
    remote_jid = data.get("key").get("remoteJid")

    # Captura do nome de usuário
    userName = data.get("pushName")

    await send_text_message(
        instance_name=chatbot_instance_name,
        number=remote_jid,
        text=get_default_message(userName),
        client=client,
    )

