from httpx import AsyncClient, _exceptions

from http import HTTPStatus

from fastapi.exceptions import HTTPException

from settings.settings import Settings

from services.http_status.http import verify_status_http

from pathlib import Path

evolution_api_url = Settings().EVOLUTION_API_URL
apikey = Settings().EVOLUTION_AUTHENTICATION_API_KEY



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

    message_type : str

    if ("conversation" in message_context):
        message_type="conversation"
    elif ("imageMessage" in message_context):
        message_type = "image"


    return message_type

