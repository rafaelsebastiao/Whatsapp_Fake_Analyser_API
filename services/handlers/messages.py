import json

from pathlib import Path

from services.evolution.messages import  send_text_message, get_message_type

from services.evolution.chats import find_bot_messages, get_last_message_info

from services.timecalc.time import has_passed_24_hours

from settings.settings import Settings

from services.ai.genai import text_analisys

base_path = Path().cwd()

greetings_file_path = base_path / "templates" / "greetings.json"

text_analisys_message_path = base_path / "templates" / "text_analysis_message.json"

image_analisys_message_path = base_path / "templates" / "image_analysis_message.json"

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
    
    

async def handle_message_upsert(payload: dict, client):
    base64_user_message : str
    text_user_message: str

    # Captura do json retornado pelo webhook assim que é detectado uma mensagem para o bot
    data = payload.get("data")

    # Captura do número de telefone
    remote_jid = data.get("key").get("remoteJid")

    # Captura do nome de usuário
    user_name = data.get("pushName")
    
    # Verificar tipo da mensagem
    user_message_type = get_message_type(data)

    # Histórico de mensagens enviadas pelo bot para o número do usuário
    bot_history_messages = await find_bot_messages(
        instance_name=chatbot_instance_name,
        number=remote_jid,
        client=client
    )

    
    # Lista de mensagens enviadas pelo bot para o número do usuário
    bot_history_messages_list = bot_history_messages.get("messages").get("records")
        
    if len(bot_history_messages_list):

        # Retorna um dict com o conteúdo e com o timestamp da ultima mensagem {'content': text, 'timestamp': timestamp}
        last_bot_message_info = get_last_message_info(bot_history_messages_list)
                                    
        # # Retorna o conteúdo da última mensagem do bot ao usuário
        # last_bot_message_content = last_bot_message_info.get("content")
                                    
        # Retorna o timestamp da última mensagem do bot ao usuário
        last_bot_message_timestamp = last_bot_message_info.get("timestamp")
                        
        # User Header padrão com o nome do usuário (Olá, fulano...)
        # user_header = get_user_header(user_name)
                
    match user_message_type:
            # Caso a mensagem que o usuário enviou for uma imagem
            case "image":
                base64_user_message = data.get("message").get("base64")
                
                # Se o bot ainda não enviou mensagens para o usuário, será enviado a mensagem padrão
                if not len(bot_history_messages_list):
                    await send_text_message(
                        instance_name=chatbot_instance_name,
                        number=remote_jid,
                        text=get_default_message(user_name),
                        client=client        
                    )

                    await send_text_message(
                        instance_name=chatbot_instance_name,
                        number=remote_jid,
                        text=get_image_analysis_message(),
                        client=client        
                    )

                    #TODO analisar a imagem
                
                
                elif has_passed_24_hours(last_bot_message_timestamp):
                    await send_text_message(
                        instance_name=chatbot_instance_name,
                        number=remote_jid,
                        text=get_default_message(user_name),
                        client=client        
                    )
                    await send_text_message(
                        instance_name=chatbot_instance_name,
                        number=remote_jid,
                        text=get_image_analysis_message(),
                        client=client        
                    )

                    #TODO analisar a imagem
                else:
                    await send_text_message(
                        instance_name=chatbot_instance_name,
                        number=remote_jid,
                        text=get_image_analysis_message(),
                        client=client        
                    )
                    
                    #TODO analisar a imagem
                    
            case "conversation":
                user_text_message = data.get("message").get("conversation")
    
                if not len(bot_history_messages_list):
                    await send_text_message(
                        instance_name=chatbot_instance_name,
                        number=remote_jid,
                        text=get_default_message(user_name),
                        client=client        
                    )

                elif has_passed_24_hours(last_bot_message_timestamp):
                    await send_text_message(
                        instance_name=chatbot_instance_name,
                        number=remote_jid,
                        text=get_default_message(user_name),
                        client=client        
                    )
                    await send_text_message(
                        instance_name=chatbot_instance_name,
                        number=remote_jid,
                        text=get_text_analysis_message(),
                        client=client        
                    )

                    #TODO analisar o texto enviado pelo usuário
                else:
                    await send_text_message(
                        instance_name=chatbot_instance_name,
                        number=remote_jid,
                        text=get_text_analysis_message(),
                        client=client        
                    )

                    #TODO analisar o texto enviado pelo usuário