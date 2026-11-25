import pytest

from services.handlers.parser import MessageType, parse_message


def test_conversation_e_texto():
    parsed = parse_message({"message": {"conversation": "Vacina causa autismo?"}})

    assert parsed.type is MessageType.TEXT
    assert parsed.text == "Vacina causa autismo?"


def test_conversation_com_message_context_info():
    parsed = parse_message({
        "message": {"conversation": "oi", "messageContextInfo": {"deviceListMetadata": {}}}
    })

    assert parsed.type is MessageType.TEXT
    assert parsed.text == "oi"


def test_extended_text_message_com_link_e_texto():
    parsed = parse_message({
        "message": {
            "extendedTextMessage": {
                "text": "Olha isso https://exemplo.com/noticia",
                "matchedText": "https://exemplo.com/noticia",
            }
        }
    })

    assert parsed.type is MessageType.TEXT
    assert parsed.text == "Olha isso https://exemplo.com/noticia"


def test_extended_text_message_citando_mensagem_e_texto():
    parsed = parse_message({
        "message": {
            "extendedTextMessage": {
                "text": "Isso é verdade?",
                "contextInfo": {"quotedMessage": {"conversation": "Notícia citada"}},
            }
        }
    })

    assert parsed.type is MessageType.TEXT
    assert parsed.text == "Isso é verdade?"


def test_mensagem_temporaria_e_desembrulhada():
    parsed = parse_message({
        "message": {"ephemeralMessage": {"message": {"conversation": "texto temporário"}}}
    })

    assert parsed.type is MessageType.TEXT
    assert parsed.text == "texto temporário"


def test_imagem_com_legenda_e_base64():
    parsed = parse_message({
        "message": {
            "imageMessage": {"caption": "Essa foto é real?", "mimetype": "image/jpeg"},
            "base64": "aGVsbG8=",
        }
    })

    assert parsed.type is MessageType.IMAGE
    assert parsed.caption == "Essa foto é real?"
    assert parsed.base64 == "aGVsbG8="


@pytest.mark.parametrize("key", [
    "audioMessage",
    "stickerMessage",
    "videoMessage",
    "documentMessage",
    "locationMessage",
    "contactMessage",
])
def test_tipos_nao_suportados(key):
    parsed = parse_message({"message": {key: {}, "messageContextInfo": {}}})

    assert parsed.type is MessageType.UNSUPPORTED


@pytest.mark.parametrize("data", [
    None,
    {},
    {"message": None},
    {"message": {}},
    {"message": "texto solto"},
    {"message": {"messageContextInfo": {}}},
    {"message": {"conversation": ""}},
    {"message": {"conversation": "   "}},
    {"message": {"conversation": None}},
    {"message": {"extendedTextMessage": None}},
])
def test_message_vazio_ou_invalido_e_ignorado(data):
    assert parse_message(data).type is MessageType.IGNORED


@pytest.mark.parametrize("key", [
    "reactionMessage",
    "protocolMessage",
    "editedMessage",
])
def test_eventos_sem_conteudo_sao_ignorados(key):
    parsed = parse_message({"message": {key: {"key": {"id": "ABC"}}, "messageContextInfo": {}}})

    assert parsed.type is MessageType.IGNORED
