from services.evolution.messages import send_default_text_message, send_analysis_message, get_message_type, send_prohibited_message_type

from services.evolution.chats import find_bot_messages, get_last_message_info

from services.timecalc.time import has_passed_24_hours

from settings.settings import Settings

from services.ai.genai import text_analisys



chatbot_instance_name = Settings().CHATBOT_INSTANCE_NAME

    
    

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

    # Retorna um dict com o conteúdo e com o timestamp da ultima mensagem {'content': text, 'timestamp': timestamp}
    last_bot_message_info = get_last_message_info(bot_history_messages_list)
                                        
    last_bot_message_timestamp = last_bot_message_info.get("timestamp")

    list_is_empty = not bot_history_messages_list
    
    passed_24h = has_passed_24_hours(last_bot_message_timestamp)

        
     
    match user_message_type:
            # Caso a mensagem que o usuário enviou for uma imagem
            case "image":
                base64_user_message = data.get("message").get("base64")
                                
                # Se o bot ainda não enviou mensagens para o usuário ou se a ultima mensagem é antiga, será enviado a mensagem padrão
                if list_is_empty or passed_24h:
                    
                    await send_default_text_message(
                        number=remote_jid,
                        user_name=user_name,
                        client=client
                    )


                await send_analysis_message(
                    number=remote_jid,
                    message_type=user_message_type,
                    client=client
                )

                #TODO analisar a imagem
                    
            case "conversation":
                user_text_message = data.get("message").get("conversation")

                # Caso a lista esteja vazia ou a ultima mensagem for antiga
                if list_is_empty or passed_24h:
                    
                    await send_default_text_message(
                        number=remote_jid,
                        user_name=user_name,
                        client=client
                    )

                # Caso a lista não seja vazia ou a mensagem for antiga
                if not list_is_empty or passed_24h:

                    await send_analysis_message(
                        number=remote_jid,
                        message_type=user_message_type,
                        client=client
                    )


                    #TODO analisar o texto enviado pelo usuário
            case _:
                await send_prohibited_message_type(
                    number=remote_jid,
                    client=client
                )
