import time

from enum import Enum

from typing import Callable


class ConversationState(str, Enum):
    IDLE = "OCIOSO"
    AWAITING_NEWS = "AGUARDANDO_NOTICIA"


class MemoryConversationStore:
    """Estado da conversa de cada usuário, em memória.

    Só quem está aguardando a notícia fica guardado; quem não está no dicionário está OCIOSO.
    A expiração é conferida na próxima mensagem do usuário (sem timer).
    """

    def __init__(self, timeout: int = 600, clock: Callable[[], float] = time.monotonic):
        self._timeout = timeout
        self._clock = clock
        # jid -> momento em que o usuário passou a AGUARDANDO_NOTICIA
        self._awaiting: dict[str, float] = {}

    def get_state(self, jid: str) -> ConversationState:
        started_at = self._awaiting.get(jid)

        if started_at is None:
            return ConversationState.IDLE

        if self.is_expired(started_at):
            self._awaiting.pop(jid, None)
            return ConversationState.IDLE

        return ConversationState.AWAITING_NEWS

    # Também usado para reiniciar os 10 minutos
    def set_awaiting(self, jid: str):
        if len(self._awaiting) > 10_000:  # limpeza preguiçosa de quem nunca voltou
            self._awaiting = {
                key: started_at for key, started_at in self._awaiting.items()
                if not self.is_expired(started_at)
            }
        self._awaiting[jid] = self._clock()

    def reset(self, jid: str):
        self._awaiting.pop(jid, None)

    def is_expired(self, started_at: float) -> bool:
        return self._clock() - started_at >= self._timeout
