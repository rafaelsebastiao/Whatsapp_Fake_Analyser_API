from httpx import AsyncClient, _exceptions

from http import HTTPStatus

from fastapi.exceptions import HTTPException

from settings.settings import Settings

from services.http_status.http import verify_status_http


evolution_api_url = Settings().EVOLUTION_API_URL
apikey = Settings().EVOLUTION_AUTHENTICATION_API_KEY

# Método para retornar informações da ultima mensagem enviada pelo bot -> Seu conteúdo e seu timestamp
def get_last_message_info(bot_history_messages : list) -> dict:
    if not len(bot_history_messages):
        return {}
    # Retorna a mensagem ("records") com o último timestamp 
    last_message = max(
        bot_history_messages,
        key=lambda message: message.get("messageTimestamp", 0)
    )

    content = last_message.get("message").get("conversation")
    timestamp = last_message.get("messageTimestamp")

    return {
        "content" : content,
        "timestamp":timestamp
    }



async def find_bot_messages(
        instance_name: str,     
        number:str,
        client:AsyncClient
        
        ):
    try:
        response = await client.post(
            url=f'{evolution_api_url}/chat/findMessages/{instance_name}/',
            json={
                 "where": {
                    "key": {
                        "remoteJid": number,
                        "fromMe": True
                    }
                }
            },

            headers={'apikey':apikey}
            )
    except _exceptions.ConnectError as errc:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
            detail=f"Connection error: The Whatsapp's endpoint is inaccessible or down!\n"
                            
        )

    verify_status_http(response)
    return response.json()

    