import pytest

from services.conversation.state import ConversationState, MemoryConversationStore

from services.evolution.messages import get_template

from services.handlers import conversation

from services.handlers.parser import MessageType, ParsedMessage


pytestmark = pytest.mark.anyio

JID = "5511999999999@s.whatsapp.net"

MENU = get_template("menu")


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class FakeGemini:
    def __init__(self):
        self.result: str | None = "Resultado: a notícia é FALSA."
        self.calls: list[str] = []

    async def __call__(self, notice: str, client) -> str | None:
        self.calls.append(notice)
        return self.result


@pytest.fixture
def sent(monkeypatch):
    messages: list[str] = []

    async def fake_send_text_message(instance_name, number, text, client):
        assert number == JID
        messages.append(text)
        return {}

    monkeypatch.setattr(conversation, "send_text_message", fake_send_text_message)
    return messages


@pytest.fixture
def gemini(monkeypatch):
    fake = FakeGemini()
    monkeypatch.setattr(conversation, "analyse_news", fake)
    return fake


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def store(clock):
    return MemoryConversationStore(timeout=600, clock=clock)


def text(value: str) -> ParsedMessage:
    return ParsedMessage(MessageType.TEXT, text=value)


IMAGE = ParsedMessage(MessageType.IMAGE, caption="foto", base64="aGVsbG8=")
AUDIO = ParsedMessage(MessageType.UNSUPPORTED)
IGNORED = ParsedMessage(MessageType.IGNORED)


async def receive(store, parsed, user_name="Maria"):
    await conversation.handle_conversation(JID, user_name, parsed, store, client=None)


def awaiting(store) -> bool:
    return store.get_state(JID) is ConversationState.AWAITING_NEWS


# ---------- OCIOSO ----------

async def test_ocioso_qualquer_mensagem_envia_saudacao_e_menu_numa_mensagem(store, sent, gemini):
    await receive(store, text("oi"))

    assert len(sent) == 1
    assert "Olá Maria" in sent[0]
    assert MENU in sent[0]
    assert not awaiting(store)
    assert gemini.calls == []


async def test_ocioso_sem_push_name_nao_escreve_none(store, sent, gemini):
    await receive(store, text("oi"), user_name=None)

    assert "None" not in sent[0]
    assert "Olá, tudo bem?" in sent[0]


@pytest.mark.parametrize("parsed", [AUDIO, IMAGE], ids=["audio_figurinha", "imagem"])
async def test_ocioso_midia_envia_saudacao_e_menu(store, sent, gemini, parsed):
    await receive(store, parsed)

    assert len(sent) == 1
    assert MENU in sent[0]
    assert not awaiting(store)


@pytest.mark.parametrize("option", ["1", " 1 "])
async def test_ocioso_opcao_1_pede_noticia_e_aguarda(store, sent, gemini, option):
    await receive(store, text(option.strip()))

    assert sent == [get_template("request_text")]
    assert awaiting(store)


async def test_ocioso_opcao_2_avisa_em_desenvolvimento_e_reenvia_menu(store, sent, gemini):
    await receive(store, text("2"))

    assert len(sent) == 1
    assert get_template("image_in_development") in sent[0]
    assert MENU in sent[0]
    assert not awaiting(store)


async def test_ocioso_opcao_3_explica_e_mostra_menu(store, sent, gemini):
    await receive(store, text("3"))

    assert len(sent) == 1
    assert get_template("how_it_works") in sent[0]
    assert MENU in sent[0]
    assert not awaiting(store)


@pytest.mark.parametrize("value", ["0", "menu", "4", "1 - Analisar texto"])
async def test_ocioso_outros_textos_mostram_saudacao_e_menu(store, sent, gemini, value):
    await receive(store, text(value))

    assert len(sent) == 1
    assert "Olá Maria" in sent[0]
    assert not awaiting(store)


async def test_ocioso_evento_sem_conteudo_e_ignorado(store, sent, gemini):
    await receive(store, IGNORED)

    assert sent == []
    assert not awaiting(store)


# ---------- AGUARDANDO_NOTICIA ----------

async def test_aguardando_texto_e_analisado_e_volta_a_ocioso(store, sent, gemini):
    store.set_awaiting(JID)

    await receive(store, text("Vacina causa autismo"))

    assert gemini.calls == ["Vacina causa autismo"]
    assert sent == [
        get_template("text_analysis_message"),
        "Resultado: a notícia é FALSA.",
        get_template("analysis_done"),
    ]
    assert not awaiting(store)


async def test_aguardando_link_e_analisado(store, sent, gemini):
    store.set_awaiting(JID)

    await receive(store, text("https://exemplo.com/noticia"))

    assert gemini.calls == ["https://exemplo.com/noticia"]
    assert not awaiting(store)


async def test_aguardando_texto_longo_e_analisado_sem_limite(store, sent, gemini):
    store.set_awaiting(JID)
    long_text = "notícia " * 5_000

    await receive(store, text(long_text))

    assert gemini.calls == [long_text]


async def test_aguardando_opcao_do_menu_e_analisada_como_texto(store, sent, gemini):
    store.set_awaiting(JID)

    await receive(store, text("1"))

    assert gemini.calls == ["1"]


@pytest.mark.parametrize("value", ["0", "menu", "MENU", "Menu"])
async def test_aguardando_0_ou_menu_cancela_e_mostra_menu(store, sent, gemini, value):
    store.set_awaiting(JID)

    await receive(store, text(value))

    assert len(sent) == 1
    assert get_template("analysis_canceled") in sent[0]
    assert MENU in sent[0]
    assert gemini.calls == []
    assert not awaiting(store)


async def test_aguardando_imagem_avisa_e_continua_aguardando(store, sent, gemini):
    store.set_awaiting(JID)

    await receive(store, IMAGE)

    assert sent == [get_template("image_not_supported")]
    assert gemini.calls == []
    assert awaiting(store)


async def test_aguardando_audio_ou_figurinha_avisa_e_continua_aguardando(store, sent, gemini):
    store.set_awaiting(JID)

    await receive(store, AUDIO)

    assert sent == [get_template("prohibited_message_type")]
    assert awaiting(store)


async def test_aguardando_evento_sem_conteudo_e_ignorado(store, sent, gemini):
    store.set_awaiting(JID)

    await receive(store, IGNORED)

    assert sent == []
    assert awaiting(store)


async def test_aguardando_falha_do_gemini_avisa_e_reinicia_os_10_minutos(store, sent, gemini, clock):
    store.set_awaiting(JID)
    gemini.result = None

    clock.now += 500
    await receive(store, text("notícia"))

    assert sent == [get_template("text_analysis_message"), get_template("analysis_failed")]
    assert awaiting(store)

    # 500 + 599 segundos desde o início: só continua aguardando porque o tempo reiniciou
    clock.now += 599
    assert awaiting(store)
    clock.now += 1
    assert not awaiting(store)


async def test_aguardando_expira_em_10_minutos_e_volta_a_ocioso(store, sent, gemini, clock):
    store.set_awaiting(JID)
    clock.now += 600

    await receive(store, text("Notícia enviada tarde demais"))

    assert gemini.calls == []
    assert len(sent) == 1
    assert MENU in sent[0]
    assert not awaiting(store)


async def test_fluxo_completo_menu_noticia_e_menu_de_novo(store, sent, gemini):
    await receive(store, text("oi"))
    await receive(store, text("1"))
    await receive(store, text("Notícia"))
    await receive(store, text("obrigado"))

    assert gemini.calls == ["Notícia"]
    assert MENU in sent[0]
    assert sent[1] == get_template("request_text")
    assert sent[-2] == get_template("analysis_done")
    assert MENU in sent[-1]
    assert not awaiting(store)
