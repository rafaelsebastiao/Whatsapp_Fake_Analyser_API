import json

from pathlib import Path

from services.evolution.messages import  send_text_message

from services.evolution.chats import find_bot_messages, get_last_message_info

from settings.settings import Settings

base_path = Path().cwd()

greetings_file_path = base_path / "templates" / "greetings.json"

evolution_api_url = Settings().EVOLUTION_API_URL

evolution_api_key = Settings().EVOLUTION_AUTHENTICATION_API_KEY

chatbot_instance_name = Settings().CHATBOT_INSTANCE_NAME


# Método que lê o json de mensagens padrão que serão enviadas pelo bot
def get_default_message(userName:str) -> str:
    with open(greetings_file_path, 'r', encoding='utf-8') as file:
        content = json.load(file)

    message = f'🤖 Olá {userName}, tudo bem?\n{content["text"]}'
    return message


def get_user_header(user_name:str) -> str:
    return f'🤖 Olá {user_name}, tudo bem?\n'


async def handle_message_upsert(payload: dict, client):
    # Captura do json retornado pelo webhook assim que é detectado uma mensagem para o bot
    data = payload.get("data")

    # Captura do número de telefone
    remote_jid = data.get("key").get("remoteJid")

    # Captura do nome de usuário
    user_name = data.get("pushName")

    # Histórico de mensagens enviadas pelo bot para o número do usuário
    bot_history_messages = await find_bot_messages(
        instance_name=chatbot_instance_name,
        number=remote_jid,
        client=client
    )

    # Lista de mensagens enviadas pelo bot para o número do usuário
    bot_history_messages_list = bot_history_messages.get("messages").get("records")

    # Se o bot ainda não enviou mensagens para o usuário, será enviado a mensagem padrão
    if not len(bot_history_messages_list):
        send_message = get_default_message(user_name)    
    else:
        
        # Retorna um dict com o conteúdo e com o timestamp da ultima mensagem {'content': text, 'timestamp': timestamp}
        last_message_info = get_last_message_info(bot_history_messages_list)

        # Retorna o conteúdo da última mensagem
        last_message_content = last_message_info.get("content")

        # User Header padrão com o nome do usuário (Olá, fulano...)
        user_header = get_user_header(user_name)

        
         
        #TODO 1. Comparar o timestamp da mensagem do bot com a data e hora atual (Exemplo: Manda o olá se a ultima mensagem do bot foi a um dia atrás independentemente do conteúdo dela) 
        
        # Irá cair aqui no else do timestamp, ou seja, se a mensagem é recente
        if user_header in last_message_content:
            '''
                TODO
                  
                    2. Se a ultima mensagem do bot foi recente e foi um olá, devo criar a lógica de análise da ultima mensagem que O USUÁRIO ENVIOU

                    CRIAR LÓGICA DA ANÁLISE DA MENSAGEM ENVIADA PELO USUÁRIO 

            '''
  
        else:
            send_message = get_default_message(user_name)
    

    await send_text_message(
        instance_name=chatbot_instance_name,
        number=remote_jid,
        text=send_message,
        client=client,
    )

