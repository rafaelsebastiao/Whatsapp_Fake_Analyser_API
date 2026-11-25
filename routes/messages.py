from fastapi import APIRouter, Depends, BackgroundTasks

from fastapi.requests import Request

from dependencies.http import get_http_client

from dependencies.cordination import get_coordinator

from dependencies.conversation import get_conversation_store

from services.handlers.messages import dispatch_message


router = APIRouter(
    prefix='/messages',
    tags = ['messages']
)


@router.post('/new-message/')
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    client = Depends(get_http_client),
    coord =  Depends(get_coordinator),
    store = Depends(get_conversation_store)
   ):

    payload = await request.json()

    event = payload.get("event")

    # Mensagem nova recebida: enfileira para a máquina de estados da conversa
    if event == "messages.upsert":
        await dispatch_message(payload, client, coord, store, background_tasks)
