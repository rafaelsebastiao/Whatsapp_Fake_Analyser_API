from services.conversation.state import ConversationState, MemoryConversationStore


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def make_store():
    clock = FakeClock()
    return MemoryConversationStore(timeout=600, clock=clock), clock


def test_usuario_novo_esta_ocioso():
    store, _ = make_store()

    assert store.get_state("5511@s.whatsapp.net") is ConversationState.IDLE


def test_set_awaiting_e_reset():
    store, _ = make_store()

    store.set_awaiting("user")
    assert store.get_state("user") is ConversationState.AWAITING_NEWS

    store.reset("user")
    assert store.get_state("user") is ConversationState.IDLE


def test_continua_aguardando_antes_de_10_minutos():
    store, clock = make_store()
    store.set_awaiting("user")

    clock.now += 599
    assert store.get_state("user") is ConversationState.AWAITING_NEWS


def test_expira_em_10_minutos():
    store, clock = make_store()
    store.set_awaiting("user")

    clock.now += 600
    assert store.get_state("user") is ConversationState.IDLE
    # A expiração remove o usuário: continua ocioso mesmo se o relógio "voltar"
    clock.now -= 600
    assert store.get_state("user") is ConversationState.IDLE


def test_set_awaiting_de_novo_reinicia_o_tempo():
    store, clock = make_store()
    store.set_awaiting("user")

    clock.now += 500
    store.set_awaiting("user")
    clock.now += 500

    assert store.get_state("user") is ConversationState.AWAITING_NEWS


def test_estado_e_separado_por_usuario():
    store, _ = make_store()
    store.set_awaiting("a")

    assert store.get_state("a") is ConversationState.AWAITING_NEWS
    assert store.get_state("b") is ConversationState.IDLE
