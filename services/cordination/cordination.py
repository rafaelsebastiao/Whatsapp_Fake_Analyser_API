# services/coordination.py
import logging
import time
from collections import deque
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)

class MemoryCoordinator:
    def __init__(self, dedup_ttl: int = 300):
        self._dedup_ttl = dedup_ttl
        self._seen: dict[str, float] = {}
        self._queues: dict[str, deque] = {}
        self._active: set[str] = set()

    async def is_duplicate(self, message_id: str) -> bool:
        now = time.monotonic()
        if len(self._seen) > 10_000:  # limpeza preguiçosa
            self._seen = {k: v for k, v in self._seen.items() if v > now}
        if self._seen.get(message_id, 0) > now:
            return True
        self._seen[message_id] = now + self._dedup_ttl
        return False

    async def enqueue(self, jid: str, payload: dict) -> bool:
        """Retorna True se este chamador deve iniciar o processamento do usuário."""
        self._queues.setdefault(jid, deque()).append(payload)
        if jid in self._active:
            return False
        self._active.add(jid)
        return True

    async def drain(self, jid: str, handler: Callable[[dict], Awaitable[None]]):
        queue = self._queues[jid]
        try:
            while queue:
                payload = queue.popleft()
                try:
                    await handler(payload)
                except Exception:
                    logger.exception("Erro ao processar mensagem de %s", jid)
        finally:
            self._active.discard(jid)
            if not queue:
                self._queues.pop(jid, None)