from services.conversation.state import MemoryConversationStore

_store = MemoryConversationStore()

def get_conversation_store() -> MemoryConversationStore:
    return _store
