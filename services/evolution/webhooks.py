from httpx import AsyncClient, _exceptions

from http import HTTPStatus

from fastapi.exceptions import HTTPException

from settings.settings import Settings

from services.http_status.http import verify_status_http



# Eventos de Webhook Evolution API

'''
Instância e conexão
APPLICATION_STARTUP: a API foi iniciada.
QRCODE_UPDATED: um novo QR Code foi gerado.
CONNECTION_UPDATE: mudou o estado da conexão (open, connecting, close).
REMOVE_INSTANCE: a instância foi removida.
LOGOUT_INSTANCE: a instância fez logout.
NEW_JWT_TOKEN: um novo token JWT foi gerado.

Mensagens
MESSAGES_SET: carga inicial do histórico de mensagens.
MESSAGES_UPSERT: mensagem nova recebida (o mais usado).
MESSAGES_UPDATE: mudança de status da mensagem (entregue, lida).
MESSAGES_EDITED: mensagem editada.
MESSAGES_DELETE: mensagem apagada.
SEND_MESSAGE: mensagem enviada pela instância.
SEND_MESSAGE_UPDATE: atualização de uma mensagem enviada.
Contatos e presença
CONTACTS_SET: carga inicial de contatos.
CONTACTS_UPSERT: contato novo ou atualizado.
CONTACTS_UPDATE: alteração em um contato.
PRESENCE_UPDATE: presença (online, digitando, gravando áudio).

Chats
CHATS_SET: carga inicial de conversas.
CHATS_UPSERT: conversa nova ou atualizada.
CHATS_UPDATE: alteração em uma conversa.
CHATS_DELETE: conversa apagada.

Grupos
GROUPS_UPSERT: grupo criado ou atualizado.
GROUP_UPDATE: alteração nas informações do grupo.
GROUP_PARTICIPANTS_UPDATE: entrada, saída, promoção ou remoção de participantes.

Outros
LABELS_EDIT: etiqueta criada ou editada.
LABELS_ASSOCIATION: etiqueta associada a um chat.
CALL: chamada recebida.
TYPEBOT_START e TYPEBOT_CHANGE_STATUS: integração com Typebot.
'''

own_api_url = Settings().OWN_API_URL
evolution_api_url = Settings().EVOLUTION_API_URL
apikey = Settings().EVOLUTION_AUTHENTICATION_API_KEY

async def create_webhook(instance_name:str, client:AsyncClient):
    try:
        print(f'{evolution_api_url}/webhook/set/{instance_name}')


        response = await client.post(
            url = f'{evolution_api_url}/webhook/set/{instance_name}',
            
            json={
                "webhook" : {
                    "enabled": True,
                    "url": f"{own_api_url}/messages/new-message/",
                    "events": [
                    "MESSAGES_UPSERT"
                    ],
                    
                    "headers": {
                        "apikey": apikey
                        },
                    "base64": True
                }
               
            },

            headers={
                "apikey": apikey
            },
            timeout=30
        )

    except _exceptions.ConnectError as errc:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
            detail=f"Connection error: The Whatsapp's endpoint is inaccessible or down!\n"
            )
            
    verify_status_http(response)
    return response





# Método que retorna o webhook de uma instância. Retornará None caso a instância não possua um
async def get_webhook(instance_name:str, client: AsyncClient):
    try:
        response = await client.get(
            url = f'{evolution_api_url}/webhook/find/{instance_name}/',
            headers={
                "apikey": apikey
            },
            timeout=5
        )

    except _exceptions.ConnectError as errc:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
            detail=f"Connection error: The Whatsapp's endpoint is inaccessible or down!\n"
            )

    verify_status_http(response)
    return response