from fastapi import APIRouter, Depends

from dependencies.http import get_http_client

from services.evolution.instances import find_instances, create_instance, connect_instance

from services.evolution.webhooks import get_webhook, create_webhook

router = APIRouter(
    prefix='/instances',
    tags = ['Instances']
)


@router.get('/chatbot/')
async def connect_chatbot(
    client = Depends(get_http_client)
): 
    

    response = await find_instances(client=client)
    instances_list = response.json()

    #Se não houver sessões, deverá ser criado uma
    if not len(instances_list):
        await create_instance(name="fake-analyser-chatbot", client=client)

        #Alterar a lista de instâncias com a instância nova
        response = await find_instances(client=client)
        instances_list = response.json()

    # Captura o nome da primeira instância que encontrar
    instance_name = instances_list[0]["name"]


    # Realiza a conexão da instância
    response = await connect_instance(name=instance_name, client=client)

    
    # Verificação se existe ou não o webhook
    webhook_response = await get_webhook(instance_name=instance_name, client=client)


    
    #Se não existe webhook associado a instância, deve ser criado um
    if webhook_response.json() is None:
        await create_webhook(instance_name=instance_name, client=client)
    
    return response.json()