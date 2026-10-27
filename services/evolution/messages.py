import json

from httpx import AsyncClient, _exceptions

from http import HTTPStatus

from fastapi.exceptions import HTTPException

from settings.settings import Settings

from services.http_status.http import verify_status_http

from pathlib import Path

base_path = Path().cwd()

greetings_file_path = base_path / "templates" / "greetings.json"

text_analisys_message_path = base_path / "templates" / "text_analysis_message.json"

image_analisys_message_path = base_path / "templates" / "image_analysis_message.json"

prohibited_message_type_path = base_path / "templates" / "prohibited_message_type.json"

evolution_api_url = Settings().EVOLUTION_API_URL
apikey = Settings().EVOLUTION_AUTHENTICATION_API_KEY
chatbot_instance_name = Settings().CHATBOT_INSTANCE_NAME




# Método que envia para o usuário a mensagem padrão já definida pelo sistema.
async def send_default_text_message(
    number:str, 
    user_name:str,
    client:AsyncClient

):
    default_text = get_default_message(user_name)

    response = await send_text_message(
        instance_name=chatbot_instance_name,
        number=number,
        text=default_text,
        client=client
    )

    return response


async def send_analysis_message(
    number:str,
    client:AsyncClient,
    message_type:str):

    match (message_type):
        case "image":
            response = await send_text_message(
                 instance_name=chatbot_instance_name,
                 number=number,
                 text=get_image_analysis_message(),
                 client=client
            )

        case "conversation":
            response = await send_text_message(
                instance_name=chatbot_instance_name,
                number=number,
                text=get_text_analysis_message(),
                client=client
            )
    

    return response


async def send_prohibited_message_type(
    number:str,
    client:AsyncClient
):
    response = await send_text_message(
        instance_name=chatbot_instance_name,
        number=number,
        text=get_prohibited_message_type(),
        client=client
    )

    return response


async def send_text_message(
    instance_name: str,
    number:str,
    text:str, 
    client:AsyncClient
        ):
    
    try:
        response = await client.post(
            url = f'{evolution_api_url}/message/sendText/{instance_name}',
            json={
                "number":number,
                "text":text
            },

            headers={
                "apikey":apikey
            },

            timeout=15
        )
    except _exceptions.ConnectError as errc:
                    raise HTTPException(
                        status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
                        detail=f"Connection error: The Whatsapp's endpoint is inaccessible or down!\n"
                        
                    )
        
    verify_status_http(response)
    return response.json()



def get_message_type(data: dict):
    message_context = data.get("message")

    message_type : str = ''

    if ("conversation" in message_context):
        message_type="conversation"
    elif ("imageMessage" in message_context):
        message_type = "image"


    return message_type



# Método que lê o json de mensagens padrão que serão enviadas pelo bot
def get_default_message(user_name:str) -> str:
    with open(greetings_file_path, 'r', encoding='utf-8') as file:
        content = json.load(file)

    message = f'🤖 Olá {user_name}, tudo bem?\n{content["text"]}'
    return message



def get_image_analysis_message():
    image_analisys_message:str = ''

    with open(image_analisys_message_path, 'r', encoding='utf-8') as file:
        content = json.load(file)
        image_analisys_message = content["text"]

    return image_analisys_message

def get_text_analysis_message():
    text_analisys_message:str = ''
    
    with open(text_analisys_message_path, 'r', encoding='utf-8') as file:
        content = json.load(file)
        text_analisys_message = content["text"]
    
    return text_analisys_message


def get_prohibited_message_type():
    prohibited_message_type :str = ''
    
    with open(prohibited_message_type_path, 'r', encoding='utf-8') as file:
        content = json.load(file)
        prohibited_message_type = content["text"]
    
    return prohibited_message_type
