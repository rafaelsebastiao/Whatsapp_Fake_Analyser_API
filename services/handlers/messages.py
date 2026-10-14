import json

from pathlib import Path

from services.evolution.messages import  send_text_message

from settings.settings import Settings

base_path = Path().cwd()

greetings_file_path = base_path / "templates" / "greetings.json"

evolution_api_url = Settings().EVOLUTION_API_URL

evolution_api_key = Settings().EVOLUTION_AUTHENTICATION_API_KEY

# Método que lê o json de mensagens padrão que serão enviadas pelo bot
def get_default_message():
    with open(greetings_file_path, 'r', encoding='utf-8') as file:
        content = json.load(file)

    return content["text"]




async def handle_message_upsert(payload: dict, client):
    # Captura do json retornado pelo webhook assim que é detectado uma mensagem para o bot
    data = payload.get("data")

    # Captura do número de telefone
    remote_jid = data.get("key").get("remoteJid")

    
    # print(data)
    # print(remote_jid)

    await send_text_message(
        instance_name="fake-analyser-chatbot",
        number=remote_jid,
        text=get_default_message(),
        client=client,
    )

