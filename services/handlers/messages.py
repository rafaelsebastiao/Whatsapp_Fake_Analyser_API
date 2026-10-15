import json

from pathlib import Path

from services.evolution.messages import  send_text_message

from settings.settings import Settings

from sqlalchemy import select

from sqlalchemy.orm import Session

from schemas.schemas import UserSchema

from models.models import UserModel

from database.database import get_session

base_path = Path().cwd()

greetings_file_path = base_path / "templates" / "greetings.json"

evolution_api_url = Settings().EVOLUTION_API_URL

evolution_api_key = Settings().EVOLUTION_AUTHENTICATION_API_KEY

chatbot_instance_name = Settings().CHATBOT_INSTANCE_NAME


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

    userName = data.get("pushName")

    # Buscar no banco por mensagens enviadas para este número
    with get_session() as session:

        # Pegar a ultima mensagem do usuário
        user_last_message = session.scalars(
            select(UserModel.lastMessage).where(
                UserModel.telephoneNumber == remote_jid
            )
        ).first()


        # Se ainda não foram enviadas mensagens para o usuário 
        if user_last_message is None:
            completeText = f"Olá {userName}, tudo bem?\n\n" + get_default_message()

            await send_text_message(
                instance_name=chatbot_instance_name,
                number=remote_jid,
                text=completeText,
                client=client,
            )

            '''
            TODO
                1. Criptografar o número do usuário
                2. Salvar a mensagem no banco
            '''

