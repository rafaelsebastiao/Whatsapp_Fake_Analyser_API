from dataclasses import dataclass

from enum import Enum


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    # Conteúdo que o bot não analisa (áudio, figurinha, vídeo, documento...)
    UNSUPPORTED = "unsupported"
    # Eventos sem conteúdo do usuário (reação, mensagem apagada/editada, message vazio)
    IGNORED = "ignored"


@dataclass(frozen=True)
class ParsedMessage:
    type: MessageType
    text: str | None = None
    caption: str | None = None
    base64: str | None = None


# Chaves que acompanham o conteúdo, mas não são o conteúdo em si
METADATA_KEYS = {"messageContextInfo", "senderKeyDistributionMessage", "base64"}

# Tipos que não são mensagens enviadas pelo usuário para análise
IGNORED_KEYS = {
    "reactionMessage",
    "protocolMessage",
    "editedMessage",
    "pollUpdateMessage",
    "keepInChatMessage",
    "pinInChatMessage",
    "encReactionMessage",
}

# Envelopes do WhatsApp que guardam a mensagem real em ["message"]
WRAPPER_KEYS = (
    "ephemeralMessage",
    "viewOnceMessage",
    "viewOnceMessageV2",
    "viewOnceMessageV2Extension",
    "documentWithCaptionMessage",
)


# Método que lê o "data" do webhook messages.upsert e retorna o tipo e o conteúdo da mensagem
def parse_message(data: dict | None) -> ParsedMessage:
    message = (data or {}).get("message")

    if not isinstance(message, dict):
        return ParsedMessage(MessageType.IGNORED)

    # Com "base64": true no webhook, a Evolution coloca a mídia no nível de fora
    base64 = message.get("base64")
    message = unwrap_message(message)

    if "conversation" in message:
        return text_message(message.get("conversation"))

    # Links e respostas a mensagens citadas chegam como extendedTextMessage
    if "extendedTextMessage" in message:
        return text_message((message.get("extendedTextMessage") or {}).get("text"))

    if "imageMessage" in message:
        image = message.get("imageMessage") or {}
        return ParsedMessage(
            MessageType.IMAGE,
            caption=image.get("caption"),
            base64=base64 or message.get("base64"),
        )

    content_keys = [key for key in message if key not in METADATA_KEYS]

    if not content_keys or all(key in IGNORED_KEYS for key in content_keys):
        return ParsedMessage(MessageType.IGNORED)

    return ParsedMessage(MessageType.UNSUPPORTED)


def unwrap_message(message: dict) -> dict:
    for _ in range(3):
        wrapper = next((key for key in WRAPPER_KEYS if key in message), None)
        inner = (message.get(wrapper) or {}).get("message") if wrapper else None
        if not isinstance(inner, dict):
            break
        message = inner
    return message


def text_message(text: str | None) -> ParsedMessage:
    if not isinstance(text, str) or not text.strip():
        return ParsedMessage(MessageType.IGNORED)
    return ParsedMessage(MessageType.TEXT, text=text.strip())
