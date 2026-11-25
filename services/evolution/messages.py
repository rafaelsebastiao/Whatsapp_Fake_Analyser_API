import json

from functools import cache


from httpx import AsyncClient, _exceptions

from http import HTTPStatus

from fastapi.exceptions import HTTPException

from settings.settings import Settings

from services.http_status.http import verify_status_http

from pathlib import Path

base_path = Path().cwd()

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


# Método que lê o texto de um template em templates/<name>.json
@cache
def get_template(name: str) -> str:
    with open(base_path / "templates" / f"{name}.json", 'r', encoding='utf-8') as file:
        return json.load(file)["text"]
