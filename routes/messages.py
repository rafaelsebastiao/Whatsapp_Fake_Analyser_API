from fastapi import APIRouter, Depends, BackgroundTasks

from fastapi.requests import Request

from dependencies.http import get_http_client

from services.handlers.messages import  handle_message_upsert

from settings.settings import Settings



evolution_api_url = Settings().EVOLUTION_API_URL
apikey = Settings().EVOLUTION_AUTHENTICATION_API_KEY

router = APIRouter(
    prefix='/messages',
    tags = ['messages']
)


@router.post('/new-message/')
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    client = Depends(get_http_client)
    ):

    payload = await request.json()
    event = payload.get("event")

    #Pegar a ultima conversa enviada e mandar uma mensagem de volta
    if event == "messages.upsert":
        background_tasks.add_task(handle_message_upsert, payload, client)